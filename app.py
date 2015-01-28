#!/usr/bin/env python
import os
from flask import Flask, jsonify
import requests

app = Flask(__name__)


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


def get_property_type(url):
    return url.partition('http://landregistry.data.gov.uk/def/common/')[2]


def get_query_parts(query_dict):
    query_tmpl = '  ?addr lrcommon:{} "{}"^^xsd:string.'
    query_lines = [query_tmpl.format(k, v) for k, v in query_dict.items()]
    return '\n'.join(query_lines)


@app.route('/properties/<postcode>/<street_paon_saon>', methods=['GET'])
def get_tasks(postcode, street_paon_saon):
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

    query = PPI_QUERY_TMPL.format(get_query_parts(query_dict))
    ppi_url = 'http://landregistry.data.gov.uk/landregistry/query'
    resp = requests.post(ppi_url, data={'output': 'json', 'query': query})

    sale_list = resp.json()['results']['bindings']

    if len(sale_list) == 0:
        return jsonify({'message': 'No record found.'})
    elif len(sale_list) > 1:
        return jsonify({'message': 'More then one record found.'})

    latest_sale = sale_list[0]

    result = {
        'saon': 'saon goes here',
        'paon': 'paon goes here',
        'street': 'street goes here',
        'town': 'town goes here',
        'county': 'county goes here',
        'postcode': 'postcode goes here',
        'amount': latest_sale['amount']['value'],
        'date': latest_sale['date']['value'],
        'property_type':
            get_property_type(latest_sale['property_type']['value']),
        'coordinates' : {'latitude': 99, 'longitude': 99},
    }

    return jsonify(result)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
