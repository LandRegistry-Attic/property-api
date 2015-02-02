from service.server import app, get_query_parts
import unittest
import json


import mock
import unittest
import requests
import responses

from .fake_response import FakeResponse


# see http://landregistry.data.gov.uk/app/hpi/qonsole

single_response = FakeResponse(b'''{
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

double_response = FakeResponse(b'''{
     "head": {
       "vars": [ "amount" , "date" , "property_type" ]
     } ,
     "results": {
       "bindings": [
         {
           "amount": { "datatype": "http://www.w3.org/2001/XMLSchema#integer" , "type": "typed-literal" , "value": "100000" } ,
           "date": { "datatype": "http://www.w3.org/2001/XMLSchema#date" , "type": "typed-literal" , "value": "2003-04-17" } ,
           "property_type": { "type": "uri" , "value": "http://landregistry.data.gov.uk/def/common/semi-detached" }
         },
         {
           "amount": { "datatype": "http://www.w3.org/2001/XMLSchema#integer" , "type": "typed-literal" , "value": "100001" } ,
           "date": { "datatype": "http://www.w3.org/2001/XMLSchema#date" , "type": "typed-literal" , "value": "2003-04-18" } ,
           "property_type": { "type": "uri" , "value": "http://landregistry.data.gov.uk/def/common/semi-detached" }
         }
       ]
     }
   }'''
)


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

    @mock.patch('requests.post')
    def test_search_results_calls_search_api(self, mock_post):
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

    @mock.patch('requests.post', return_value=single_response)
    def test_single_result(self, mock_post):
        search_query = "PL2%201AD/ALBERT%20ROAD_10_FLAT%202"
        response = self.app.get('/properties/%s' % search_query)

        self.assertTrue(str('100000') in str(response.data))
        self.assertTrue(str('2003-04-17') in str(response.data))

    @mock.patch('requests.post', return_value=double_response)
    def test_two_result(self, mock_post):
        search_query = "PL6%208RU/PATTINSON%20DRIVE_100"
        response = self.app.get('/properties/%s' % search_query)

        self.assertTrue(str('More then one record found.') in str(response.data))

    @mock.patch('requests.post', return_value=double_response)
    def test_unable_to_split(self, mock_post):
        search_query = "PL6%208RU/PATTINSON%20DRIVE100"

        with self.assertRaises(Exception) as context:
            response = self.app.get('/properties/%s' % search_query)

        self.assertTrue(str('Could not split combined street') in str(context.exception))
