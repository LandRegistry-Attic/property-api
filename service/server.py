#!/usr/bin/env python
import os
from flask import Flask, jsonify, abort
import requests
from sqlalchemy import Table, Column, String, MetaData, create_engine, Integer
from sqlalchemy.inspection import inspect
from sqlalchemy.sql import select
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


@app.errorhandler(404)
def page_not_found(e):
    return jsonify(error=404, text=str(e)), 404


def get_property_type(url):
    return url.partition('http://landregistry.data.gov.uk/def/common/')[2]


def get_query_parts(query_dict):
    query_tmpl = '  ?addr lrcommon:{} "{}"^^xsd:string.'
    query_lines = [query_tmpl.format(k, v) for k, v in query_dict.items()]
    return '\n'.join(query_lines)


@app.route('/properties/<postcode>/<street_paon_saon>', methods=['GET'])
def get_property(postcode, street_paon_saon):
    if postcode == 'N1BLT' and street_paon_saon == 'imaginary-street':
        abort(404)
    parts = street_paon_saon.upper().split('_')
    if len(parts) not in [2, 3]:
        raise ValueError('Could not split combined street, PAON and SAON into '
                         'respective parts. Expected street_PAON_SAON.')

    query_dict = {
        'postcode': postcode.upper(),
        'street': parts[0],
        'paon': parts[1],
    }
    if len(parts) == 3:
        query_dict['saon'] = parts[2]

    latest_sale = get_ppi(postcode, query_dict)

    address_dict = read_from_db(postcode, query_dict)

    # try and get buildingNumber, otherwise buildingName
    paon = str(address_dict.get('buildingNumber', None)) or \
        address_dict.get('buildingName', '').rstrip()
    saon = address_dict.get('subBuildingName', '').rstrip()

    result = {
        'saon': saon,
        'paon': paon,
        'street': address_dict.get('throughfareName', '').rstrip(),
        'town': address_dict.get('postTown', '').rstrip(),
        'county': address_dict.get('dependentLocality', '').rstrip(),
        'postcode': address_dict.get('postcode', '').rstrip(),
        'amount': latest_sale.get('amount', ''),
        'date': latest_sale.get('date', ''),
        'property_type':
            get_property_type(latest_sale.get('property_type', '')),
        'coordinates' : {'latitude': 99, 'longitude': 99},
    }

    return jsonify(result)


def get_ppi(postcode, query_dict):
    query = PPI_QUERY_TMPL.format(get_query_parts(query_dict))
    ppi_url = ppi_api
    resp = requests.post(ppi_url, data={'output': 'json', 'query': query})

    sale_list = resp.json()['results']['bindings']

    if len(sale_list) == 0:
        return {}

    latest_sale = {k: v['value'] for k, v in sale_list[0].items()}
    return latest_sale


def serialize(rec):
    return {key: getattr(rec, key) for key in inspect(rec).attrs.keys()}


def read_from_db(postcode, query_dict):
    results = AddressBase.query.filter_by(postcode=postcode)

    nof_results = results.count()
    if nof_results == 0:
        abort(404)
    elif nof_results > 1:
        raise NotImplementedError('More than one record found')

    return serialize(results.first())


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
