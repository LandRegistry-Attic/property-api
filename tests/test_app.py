from service.server import app, get_property_address, AddressBase

from collections import namedtuple
import json
import mock
from mock import call
from sqlalchemy.sql import or_
import requests
import responses
import unittest


from .fake_response import FakeResponse

FakeAddressBase = namedtuple('AddressBase',
                             ['subBuildingName', 'buildingNumber', 'buildingName',
                              'thoroughfareName', 'postTown', 'dependentLocality',
                              'postcode', 'positionY', 'positionX'])

zero_DB_results = []

one_DB_result = [
    FakeAddressBase('subBuildingName', 'buildingNumber', 'buildingName',
                    'thoroughfareName', 'postTown', 'dependentLocality',
                    'postcode', 'positionY', 'positionX'),
]

multiple_DB_results = [
    FakeAddressBase('subBuildingName', 'buildingNumber', 'buildingName',
                    'thoroughfareName', 'postTown', 'dependentLocality',
                    'postcode', 'positionY', 'positionX'),
    FakeAddressBase('subBuildingName', 'buildingNumber', 'buildingName',
                    'thoroughfareName', 'postTown', 'dependentLocality',
                    'postcode', 'positionY', 'positionX'),
]

FakeQuery = namedtuple('Query', ['all'])


# see http://landregistry.data.gov.uk/app/hpi/qonsole

empty_PPI_response = FakeResponse(b'''{
     "head": {
       "vars": [ "amount" , "date" , "property_type" ]
     } ,
     "results": {
       "bindings": [

       ]
     }
   }'''
)

single_PPI_response = FakeResponse(b'''{
     "head": {
       "vars": [ "amount" , "date" , "property_type" ]
     } ,
     "results": {
       "bindings": [
         {
           "amount": { "datatype": "http://www.w3.org/2001/XMLSchema#integer" , "type": "typed-literal" , "value": "100000" } ,
           "date": { "datatype": "http://www.w3.org/2001/XMLSchema#date" , "type": "typed-literal" , "value": "2003-04-17" } ,
           "property_type": { "type": "uri" , "value": "http://landregistry.data.gov.uk/def/common/semi-detached" }
         }
       ]
     }
   }'''
)

double_PPI_response = FakeResponse(b'''{
     "head": {
       "vars": [ "amount" , "date" , "property_type" ]
     } ,
     "results": {
       "bindings": [
         {
           "amount": { "datatype": "http://www.w3.org/2001/XMLSchema#integer" , "type": "typed-literal" , "value": "100001" } ,
           "date": { "datatype": "http://www.w3.org/2001/XMLSchema#date" , "type": "typed-literal" , "value": "2003-04-18" } ,
           "property_type": { "type": "uri" , "value": "http://landregistry.data.gov.uk/def/common/semi-detached" }
         },
         {
           "amount": { "datatype": "http://www.w3.org/2001/XMLSchema#integer" , "type": "typed-literal" , "value": "100000" } ,
           "date": { "datatype": "http://www.w3.org/2001/XMLSchema#date" , "type": "typed-literal" , "value": "2003-04-17" } ,
           "property_type": { "type": "uri" , "value": "http://landregistry.data.gov.uk/def/common/semi-detached" }
         }
       ]
     }
   }'''
)

address_split_error_message = 'Could not split combined street, PAON and SAON ' + \
                              'into respective parts. Expected street_PAON_SAON.'


class ViewPropertyTestCase(unittest.TestCase):

    def setUp(self):
        self.ppi_api = app.config['PPI_END_POINT']
        self.app = app.test_client()

    @mock.patch('requests.get')
    @mock.patch('requests.Response')
    def test_get_property_invalid_path_404(self, mock_response, mock_get):
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
        mock_get.return_value = mock_response
        street_address_url = "Trewithy Court"
        response = self.app.get('/properties/%s' % street_address_url)
        assert response.status_code == 404

    @mock.patch('service.server.get_property_address', return_value=one_DB_result)
    @mock.patch('requests.post')
    def test_get_property_address_called_correctly(self, mock_post, mock_get_property_address):
        search_query = "PL6%208RU/PATTINSON%20DRIVE_100"

        query_dict = {
            'postcode': 'PL6 8RU',
            'street': 'PATTINSON DRIVE',
            'paon': '100',
        }

        response = self.app.get('/properties/%s' % search_query)

        args, kwargs = mock_get_property_address.call_args

        self.assertEqual(args, (query_dict, ))
        self.assertEqual(kwargs, {})

    @mock.patch('service.server.AddressBase.query.filter_by')
    @mock.patch('service.server.AddressBase.query', return_value=FakeQuery(one_DB_result))
    def test_get_property_address_called_correctly(self, mock_query, mock_filter_by):
        query_dict = {
            'postcode': 'PL6 8RU',
            'street': 'PATTINSON DRIVE',
            'paon': '100',
        }

        get_property_address(query_dict)
        mock_filter_by.assert_has_calls(call(postcode=query_dict['postcode']))
        mock_filter_by.assert_has_calls(call(thoroughfareName=query_dict['street']))

        boolean_clauses = mock_filter_by.mock_calls[2][1][0].get_children()
        self.assertEqual(boolean_clauses[0].left.name, 'buildingNumber')
        self.assertEqual(boolean_clauses[0].right.value, query_dict['paon'])
        self.assertEqual(boolean_clauses[1].left.name, 'buildingName')
        self.assertEqual(boolean_clauses[1].right.value, query_dict['paon'])

        self.assertEqual(len(mock_filter_by.mock_calls), 4)

    @mock.patch('service.server.AddressBase.query.filter_by')
    @mock.patch('service.server.AddressBase.query', return_value=FakeQuery(one_DB_result))
    def test_get_property_address_with_saon_filters_by_subBuildingName(self, mock_query, mock_filter_by):
        query_dict = {
            'postcode': 'PL6 8RU',
            'street': 'PATTINSON DRIVE',
            'paon': '100',
            'saon': 'Flat A',
        }

        get_property_address(query_dict)
        mock_filter_by.assert_has_calls(call(subBuildingName=query_dict['saon']))

    @mock.patch('service.server.AddressBase.query', return_value=FakeQuery(zero_DB_results))
    def test_get_property_address_returns_404_when_no_results_found(self, mock_query):
        search_query = "ZZ2%201ZZ/ALBERT%20ROAD_10_FLAT%202"
        response = self.app.get('/properties/%s' % search_query)

        self.assertEqual(response.status_code, 404)

    @mock.patch('service.server.get_property_address', return_value=one_DB_result)
    @mock.patch('requests.post')
    def test_search_results_calls_search_api(self, mock_post, mock_get_property_address):
        search_query = "PL6%208RU/PATTINSON%20DRIVE_100"

        query_dict = {
            'postcode': 'PL6 8RU',
            'street': 'PATTINSON DRIVE',
            'paon': '100',
        }

        response = self.app.get('/properties/%s' % search_query)

        args, kwargs = mock_post.call_args

        self.assertIn(query_dict['postcode'], str(kwargs['data']))
        self.assertIn(query_dict['street'], str(kwargs['data']))
        self.assertIn(query_dict['paon'], str(kwargs['data']))

    @mock.patch('service.server.get_property_address', return_value=one_DB_result)
    @mock.patch('requests.post', return_value=single_PPI_response)
    def test_get_property_returns_data_from_PPI_API_when_single_result(self, mock_post, mock_get_property_address):
        search_query = "PL2%201AD/ALBERT%20ROAD_10_FLAT%202"
        response = self.app.get('/properties/%s' % search_query)

        self.assertIn('"amount": "100000"', str(response.data))
        self.assertIn('"date": "2003-04-17"', str(response.data))

    @mock.patch('service.server.get_property_address', return_value=one_DB_result)
    @mock.patch('requests.post', return_value=double_PPI_response)
    def test_get_property_returns_latest_PPI_API_result_when_more_than_one(self, mock_post, mock_get_property_address):
        search_query = "PL2%201AD/ALBERT%20ROAD_10_FLAT%202"
        response = self.app.get('/properties/%s' % search_query)

        self.assertIn('"amount": "100001"', str(response.data))
        self.assertIn('"date": "2003-04-18"', str(response.data))

    @mock.patch('service.server.get_property_address', return_value=multiple_DB_results)
    def test_get_property_returns_404_error_when_the_DB_returns_two_result(self, mock_get_property_address):
        search_query = "PL6%208RU/PATTINSON%20DRIVE_100"
        response = self.app.get('/properties/%s' % search_query)

        self.assertEqual(response.status_code, 404)

    @mock.patch('service.server.get_property_address', return_value=one_DB_result)
    @mock.patch('requests.post', return_value=empty_PPI_response)
    def test_get_property_returns_no_PPI_data_when_PPI_API_returns_empty_result(self, mock_post, mock_get_property_address):
        search_query = "PL2%201AD/ALBERT%20ROAD_10_FLAT%202"
        response = self.app.get('/properties/%s' % search_query)

        self.assertIn('"amount": null', str(response.data))
        self.assertIn('"date": null', str(response.data))
        self.assertIn('"property_type": null', str(response.data))

    def test_get_property_returns_404_response_when_no_address_delimiters(self):
        search_query = "PL6%208RU/PATTINSON%20DRIVE100"
        response = self.app.get('/properties/%s' % search_query)

        self.assertEqual(response.status_code, 404)
        self.assertIn(address_split_error_message, str(response.data))

    def test_get_property_returns_404_response_when_too_many_address_delimiters(self):
        search_query = "PL6%208RU/PAT_TIN_SON_RIVE100"
        response = self.app.get('/properties/%s' % search_query)

        self.assertEqual(response.status_code, 404)
        self.assertIn(address_split_error_message, str(response.data))
