#!/usr/bin/env python
import os
from flask import Flask, jsonify, abort
import requests
from sqlalchemy import Table, Column, String, MetaData, create_engine, Integer
from sqlalchemy.inspection import inspect
from sqlalchemy.sql import select, or_
import pg8000

from service.models import AddressBase
from service import app


ppi_api = app.config['PPI_END_POINT']


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
    # Currently the property type is the same as the end of the URL
    return url.partition('http://landregistry.data.gov.uk/def/common/')[2]


def check_field_vals(field_vals):
    if len(field_vals) not in [3, 4]:
        raise ValueError('Could not split combined street, PAON and SAON into '
                         'respective parts. Expected street_PAON_SAON.')


def get_query_dict(field_vals):
    query_dict = {
        'postcode': field_vals[0],
        'street': field_vals[1],
        'paon': field_vals[2],
    }
    if len(field_vals) == 4:
        query_dict['saon'] = field_vals[3]
    return query_dict


def get_latest_sale(query_dict):
    kv_tmpl = '  ?addr lrcommon:{} "{}"^^xsd:string.'
    kv_lines = [kv_tmpl.format(k, v.upper()) for k, v in query_dict.items()]

    query = PPI_QUERY_TMPL.format('\n'.join(kv_lines))
    ppi_url = ppi_api
    resp = requests.post(ppi_url, data={'output': 'json', 'query': query})

    sale_list = resp.json()['results']['bindings']

    if len(sale_list) == 0:
        return {}

    latest_sale = {k: v['value'] for k, v in sale_list[0].items()}
    return latest_sale


def get_property_address(query_dict):
    results = (AddressBase.query.
        filter_by(postcode=query_dict['postcode']).
        filter_by(throughfareName=query_dict['street']).
        filter(or_(
            AddressBase.buildingNumber == query_dict['paon'],
            AddressBase.buildingName == query_dict['paon'])))
    if 'saon' in query_dict:
        results = results.filter_by(subBuildingName=query_dict['saon'])

    nof_results = results.count()
    if nof_results == 0:
        abort(404)
    elif nof_results > 1:
        raise NotImplementedError('More than one record found')

    return results.first()


def create_json(address_rec, latest_sale):
    # try and get buildingNumber, otherwise buildingName
    paon = address_rec.buildingNumber or address_rec.buildingName.rstrip()

    result = {
        'saon': address_rec.subBuildingName.rstrip(),
        'paon': paon,
        'street': address_rec.throughfareName.rstrip(),
        'town': address_rec.postTown.rstrip(),
        'county': address_rec.dependentLocality.rstrip(),
        'postcode': address_rec.postcode.rstrip(),
        'amount': latest_sale.get('amount', ''),
        'date': latest_sale.get('date', ''),
        'property_type':
            get_property_type(latest_sale.get('property_type', '')),
        'coordinates' : {
            'latitude': address_rec.positionY,
            'longitude': address_rec.positionX,
        },
    }
    return result


@app.route('/properties/<postcode>/<street_paon_saon>', methods=['GET'])
def get_property(postcode, street_paon_saon):
    # TODO: remove this
    if postcode == 'N1BLT' and street_paon_saon == 'imaginary-street':
        abort(404)

    field_vals = [postcode] + street_paon_saon.split('_')
    check_field_vals(field_vals)
    query_dict = get_query_dict(field_vals)

    latest_sale = get_latest_sale(query_dict)
    address_rec = get_property_address(query_dict)

    result = create_json(address_rec, latest_sale)

    return jsonify(result)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
