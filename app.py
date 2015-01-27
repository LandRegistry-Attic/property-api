#!/usr/bin/env python
from flask import Flask, jsonify
import requests

app = Flask(__name__)


PROPERTY_TYPES = {
    'http://landregistry.data.gov.uk/def/common/detached': 'detached',
    'http://landregistry.data.gov.uk/def/common/flat-maisonette': 'flat-maisonette',
    'http://landregistry.data.gov.uk/def/common/semi-detached': 'semi-detached',
    'http://landregistry.data.gov.uk/def/common/terraced': 'terraced',
}


# see http://landregistry.data.gov.uk/app/hpi/qonsole
PPI_QUERY_TMPL = """
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
prefix lrppi: <http://landregistry.data.gov.uk/def/ppi/>
prefix lrcommon: <http://landregistry.data.gov.uk/def/common/>

# Returns the Price Paid data from the default graph for each transaction record having
# an address with the given postcode.
# The postcode to query is set in the line - ?address_instance common:postcode "PL6 8RU"^^xsd:string .


SELECT ?paon ?saon ?street ?town ?county ?postcode ?amount ?date ?property_type
WHERE
{{
    ?transx lrppi:pricePaid ?amount ;
            lrppi:transactionDate ?date ;
            lrppi:propertyAddress ?addr ;
            lrppi:propertyType ?property_type.

{}
    ?addr lrcommon:postcode ?postcode.

    OPTIONAL {{?addr lrcommon:county ?county}}
    OPTIONAL {{?addr lrcommon:paon ?paon}}
    OPTIONAL {{?addr lrcommon:saon ?saon}}
    OPTIONAL {{?addr lrcommon:street ?street}}
    OPTIONAL {{?addr lrcommon:town ?town}}

}}
ORDER BY ?amount
"""


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

    latest_sale_date = ''
    latest_sale = None
    for sale in sale_list:
        sale_date = sale['date']['value']
        latest_sale_date = max(sale_date, latest_sale_date)
        if latest_sale_date == sale_date:
            latest_sale = sale

    result = {
        'saon': 'saon goes here',
        'paon': 'paon goes here',
        'street': 'street goes here',
        'town': 'town goes here',
        'county': 'county goes here',
        'postcode': 'postcode goes here',
        'amount': latest_sale['amount']['value'],
        'date': latest_sale['date']['value'],
        'property_type': PROPERTY_TYPES[latest_sale['property_type']['value']],
        'coordinates' : {'latitude': 99, 'longitude': 99},
    }

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
