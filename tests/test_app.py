from service.server import app

from collections import namedtuple
import json
import mock
import requests
import responses
import unittest


from .fake_response import FakeResponse

AddressBase = namedtuple('AddressBase',
                         ['subBuildingName', 'buildingNumber', 'buildingName',
                          'throughfareName', 'postTown', 'dependentLocality',
                          'postcode', 'positionY', 'positionX'])
one_DB_result = [
    AddressBase('subBuildingName', 'buildingNumber', 'buildingName',
                'throughfareName', 'postTown', 'dependentLocality',
                'postcode', 'positionY', 'positionX'),
]

multiple_DB_results = [
    AddressBase('subBuildingName', 'buildingNumber', 'buildingName',
                'throughfareName', 'postTown', 'dependentLocality',
                'postcode', 'positionY', 'positionX'),
    AddressBase('subBuildingName', 'buildingNumber', 'buildingName',
                'throughfareName', 'postTown', 'dependentLocality',
                'postcode', 'positionY', 'positionX'),
]


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
    def test_get_property_calls_search_api(self, mock_post, mock_get_property_address):
        search_query = "PL6%208RU/PATTINSON%20DRIVE_100"

        query_dict = {
            'postcode': 'PL6 8RU',
            'street': 'ATTINSON DRIVE',
            'paon': '100',
        }

        response = self.app.get('/properties/%s' % search_query)

        args, kwargs = mock_post.call_args

        self.assertTrue(str(query_dict['postcode']) in str(kwargs['data']))
        self.assertTrue(str(query_dict['street']) in str(kwargs['data']))
        self.assertTrue(str(query_dict['paon']) in str(kwargs['data']))

    @mock.patch('service.server.get_property_address', return_value=one_DB_result)
    @mock.patch('requests.post', return_value=single_PPI_response)
    def test_get_property_returns_data_from_PPI_API_when_single_result(self, mock_post, mock_get_property_address):
        search_query = "PL2%201AD/ALBERT%20ROAD_10_FLAT%202"
        response = self.app.get('/properties/%s' % search_query)

        self.assertTrue(str('"amount": "100000"') in str(response.data))
        self.assertTrue(str('"date": "2003-04-17"') in str(response.data))

    @mock.patch('service.server.get_property_address', return_value=one_DB_result)
    @mock.patch('requests.post', return_value=double_PPI_response)
    def test_get_property_returns_first_PPI_API_result_when_more_than_one(self, mock_post, mock_get_property_address):
        search_query = "PL2%201AD/ALBERT%20ROAD_10_FLAT%202"
        response = self.app.get('/properties/%s' % search_query)

        self.assertTrue(str('"amount": "100001"') in str(response.data))
        self.assertTrue(str('"date": "2003-04-18"') in str(response.data))

    @mock.patch('service.server.get_property_address', return_value=multiple_DB_results)
    def test_get_property_returns_500_error_when_the_DB_returns_two_result(self, mock_get_property_address):
        search_query = "PL6%208RU/PATTINSON%20DRIVE_100"
        response = self.app.get('/properties/%s' % search_query)

        self.assertTrue(str('More than one record found') in str(response.data))

    @mock.patch('service.server.get_property_address', return_value=one_DB_result)
    @mock.patch('requests.post', return_value=empty_PPI_response)
    def test_get_property_returns_no_PPI_data_when_PPI_API_returns_empty_result(self, mock_post, mock_get_property_address):
        search_query = "PL2%201AD/ALBERT%20ROAD_10_FLAT%202"
        response = self.app.get('/properties/%s' % search_query)

        self.assertTrue(str('"amount": ""') in str(response.data))
        self.assertTrue(str('"date": ""') in str(response.data))        

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