#!/usr/bin/env python
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import os
from flask import Flask, jsonify, abort, make_response
import requests

from service import app


PPI_API = app.config['PPI_END_POINT']
ELASTIC_SEARCH_ENDPOINT = app.config['ELASTIC_SEARCH_ENDPOINT']


# see http://landregistry.data.gov.uk/app/hpi/qonsole
PPI_QUERY_TMPL = """
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
prefix lrppi: <http://landregistry.data.gov.uk/def/ppi/>
prefix lrcommon: <http://landregistry.data.gov.uk/def/common/>

# Returns the Price Paid data from the default graph for each transaction record having
# an address with the given postcode.
# The postcode to query is set in the line - ?address_instance common:postcode "PL6 8RU"^^xsd:string .


SELECT ?amount ?date ?property_type
WHERE
{{
    ?transx lrppi:pricePaid ?amount ;
            lrppi:transactionDate ?date ;
            lrppi:propertyAddress ?addr ;
            lrppi:propertyType ?property_type.
{}

}}
ORDER BY desc(?date) limit 1
"""


@app.errorhandler(Exception)
def exception_handler(e):
  return jsonify(error=500, text='{}'.format(e)), 500


@app.errorhandler(404)
def page_not_found(e):
    return jsonify(error=404, text=str(e)), 404


def get_property_type(url):
    if url:
        # Currently the property type is the same as the end of the URL
        return url.partition('http://landregistry.data.gov.uk/def/common/')[2]
    else:
        return None


def check_field_vals(field_vals):
    if len(field_vals) not in [3, 4]:
        abort(make_response('Could not split combined street, PAON and SAON '
            'into respective parts. Expected street_PAON_SAON.', 404))


def get_ppi_query_param_dict(address_rec):
    paon = address_rec.buildingNumber or address_rec.buildingName.rstrip()
    saon = address_rec.subBuildingName.rstrip()
    query_dict = {
        'postcode': address_rec.postCode.rstrip(),
        'street': address_rec.thoroughfareName.rstrip(),
        'paon': paon,
    }
    if saon:
        query_dict['saon'] = saon
    return query_dict


def get_latest_sale(query_dict):
    kv_tmpl = '  ?addr lrcommon:{} "{}"^^xsd:string.'
    kv_lines = [kv_tmpl.format(k, v.upper()) for k, v in query_dict.items()]

    query = PPI_QUERY_TMPL.format('\n'.join(kv_lines))
    resp = requests.post(PPI_API, data={'output': 'json', 'query': query})

    sale_list = resp.json()['results']['bindings']

    if len(sale_list) == 0:
        return {}

    latest_sale = {k: v['value'] for k, v in sale_list[0].items()}
    return latest_sale


def get_property_address(address_key):
    client = Elasticsearch([ELASTIC_SEARCH_ENDPOINT])
    search = Search(using=client, index='landregistry')
    query = search.filter('term', addressKey=address_key)

    return query.execute().hits


def create_json(address_rec, latest_sale):
    # try and get buildingNumber, otherwise buildingName
    paon = address_rec.buildingNumber or address_rec.buildingName.rstrip()

    result = {
        'saon': address_rec.subBuildingName.rstrip(),
        'paon': paon,
        'street': address_rec.thoroughfareName.rstrip(),
        'town': address_rec.postTown.rstrip(),
        'county': address_rec.dependentLocality.rstrip(),
        'postcode': address_rec.postCode.rstrip(),
        'amount': latest_sale.get('amount', None),
        'date': latest_sale.get('date', None),
        'property_type':
            get_property_type(latest_sale.get('property_type', None)),
        'coordinates' : {
            'latitude': address_rec.position.y,
            'longitude': address_rec.position.x,
        },
    }

    return result


@app.route('/properties/<postcode>/<joined_address_fields>', methods=['GET'])
def get_property(postcode, joined_address_fields):
    address_key = '{}_{}'.format(joined_address_fields, postcode).upper()
    address_recs = get_property_address(address_key)
    nof_results = len(address_recs)
    if nof_results != 1:
        abort(404)
    address_rec = address_recs[0]

    query_dict = get_ppi_query_param_dict(address_rec)
    latest_sale = get_latest_sale(query_dict)

    result = create_json(address_rec, latest_sale)

    return jsonify(result)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
