from service.server import app, get_property_address

from collections import namedtuple
import json
import mock
from mock import call, MagicMock
import requests
import responses
import unittest


from .fake_response import FakeResponse

FakeElasticSearchResult = namedtuple('Response', ['hits'])

FakeElasticSearchHit = namedtuple('Response', [
    'addressKey', 'buildingName','buildingNumber', 'businessName',
    'departmentName', 'dependentLocality', 'dependentThoroughfareName',
    'doubleDependentLocality', 'position', 'postCode', 'postTown',
    'subBuildingName', 'thoroughfareName', 'udprn'])

FakeQuery = namedtuple('Query', ['all'])

FakePosition = namedtuple('AttrDict', ['x', 'y'])


single_elastic_search_result = FakeElasticSearchResult(
    hits=[
        FakeElasticSearchHit(
            'address key_', 'building name_', 'building number_',
            'business name_', 'department name_', 'dependent locality_',
            'dependent thoroughfare name_', 'double dependent locality_',
            FakePosition(123.45, 543.21), 'postcode_', 'post town_',
            'sub-building name_', 'thoroughfare name_', 'udprn_',
        ),
    ]
)

empty_elastic_search_result = FakeElasticSearchResult(hits=[])

multiple_elastic_search_result = FakeElasticSearchResult(
    hits=[
        FakeElasticSearchHit(
            'address key_', 'building name_', 'building number_',
            'business name_', 'department name_', 'dependent locality_',
            'dependent thoroughfare name_', 'double dependent locality_',
            FakePosition(123.45, 543.21), 'postcode_', 'post town_',
            'sub-building name_', 'thoroughfare name_', 'udprn_',
        ),
        FakeElasticSearchHit(
            'address key_', 'building name_', 'building number_',
            'business name_', 'department name_', 'dependent locality_',
            'dependent thoroughfare name_', 'double dependent locality_',
            FakePosition(123.45, 543.21), 'postcode_', 'post town_',
            'sub-building name_', 'thoroughfare name_', 'udprn_',
        ),
    ]
)


# see http://landregistry.data.gov.uk/app/hpi/qonsole

empty_PPI_response = FakeResponse(b'''{
    "head": {
        "vars": ["amount", "date", "property_type"]
    },
    "results": {
        "bindings": []
    }
}'''
)

single_PPI_response = FakeResponse(b'''{
    "head": {
        "vars": ["amount", "date", "property_type"]
    },
    "results": {
        "bindings": [
            {
                "amount": {"datatype": "http://www.w3.org/2001/XMLSchema#integer", "type": "typed-literal", "value": "100000"},
                "date": {"datatype": "http://www.w3.org/2001/XMLSchema#date", "type": "typed-literal", "value": "2003-04-17"},
                "property_type": {"type": "uri", "value": "http://landregistry.data.gov.uk/def/common/semi-detached"}
            }
        ]
    }
}'''
)

double_PPI_response = FakeResponse(b'''{
    "head": {
        "vars": ["amount", "date", "property_type"]
    },
    "results": {
        "bindings": [
            {
                "amount": {"datatype": "http://www.w3.org/2001/XMLSchema#integer", "type": "typed-literal", "value": "100001"},
                "date": {"datatype": "http://www.w3.org/2001/XMLSchema#date", "type": "typed-literal", "value": "2003-04-18"},
                "property_type": {"type": "uri", "value": "http://landregistry.data.gov.uk/def/common/semi-detached"}
            },
            {
                "amount": {"datatype": "http://www.w3.org/2001/XMLSchema#integer", "type": "typed-literal", "value": "100000"},
                "date": {"datatype": "http://www.w3.org/2001/XMLSchema#date", "type": "typed-literal", "value": "2003-04-17"},
                "property_type": {"type": "uri", "value": "http://landregistry.data.gov.uk/def/common/semi-detached"}
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
        street_address_url = 'Trewithy Court'
        response = self.app.get('/properties/{}'.format(street_address_url))
        assert response.status_code == 404

    @mock.patch('service.server.get_property_address', return_value=single_elastic_search_result.hits)
    @mock.patch('requests.post')
    def test_get_property_address_called_correctly(self, mock_post, mock_get_property_address):
        postcode = 'PL6_8RU'
        joined_address_fields = '100_PATTINSON_DRIVE'
        expected_address_key = '{}_{}'.format(joined_address_fields, postcode)

        response = self.app.get('/properties/{}/{}'.format(postcode, joined_address_fields))

        args, kwargs = mock_get_property_address.call_args

        self.assertEqual(args, (expected_address_key, ))
        self.assertEqual(kwargs, {})

    @mock.patch('service.server.Search')
    def test_get_property_address_calls_elastic_search_correctly(self, mock_search):
        address_key = '100_PATTINSON_DRIVE_PL6_8RU'
        get_property_address(address_key)
        mock_search.return_value.filter.assert_called_once_with('term', addressKey=address_key)

    @mock.patch('service.server.Search')
    def test_get_property_address_returns_results_from_elastic_search(self, mock_search):
        mock_search.return_value.filter.return_value.execute.return_value = single_elastic_search_result
        result = get_property_address('100_PATTINSON_DRIVE_PL6_8RU')
        self.assertEqual(result, single_elastic_search_result.hits)

    @mock.patch('service.server.Search')
    def test_get_property_address_returns_404_when_no_results_found(self, mock_search):
        mock_search.return_value.filter.return_value.execute.return_value = empty_elastic_search_result

        response = self.app.get('/properties/ZZ2_1ZZ/100_PATTINSON_DRIVE')

        self.assertEqual(response.status_code, 404)

    @mock.patch('service.server.get_property_address', return_value=single_elastic_search_result.hits)
    @mock.patch('requests.post')
    def test_ppi_query_uses_faield_values_from_elastic_search(self, mock_post, mock_get_property_address):
        search_query = 'PL6%208RU/PATTINSON%20DRIVE_100'
        response = self.app.get('/properties/{}'.format(search_query))

        args, kwargs = mock_post.call_args

        first_elastic_search_hit = single_elastic_search_result.hits[0]
        ppi_query = str(kwargs['data'])
        self.assertIn(first_elastic_search_hit.postCode.upper(), ppi_query)
        self.assertIn(first_elastic_search_hit.thoroughfareName.upper(), ppi_query)
        self.assertIn(first_elastic_search_hit.buildingNumber.upper(), ppi_query)

    @mock.patch('service.server.get_property_address', return_value=single_elastic_search_result.hits)
    @mock.patch('requests.post', return_value=single_PPI_response)
    def test_get_property_returns_data_from_PPI_API_when_single_result(self, mock_post, mock_get_property_address):
        search_query = "PL2%201AD/ALBERT%20ROAD_10_FLAT%202"
        response = self.app.get('/properties/{}'.format(search_query))

        self.assertIn('"amount": "100000"', str(response.data))
        self.assertIn('"date": "2003-04-17"', str(response.data))

    @mock.patch('service.server.get_property_address', return_value=single_elastic_search_result.hits)
    @mock.patch('requests.post', return_value=double_PPI_response)
    def test_get_property_returns_latest_PPI_API_result_when_more_than_one(self, mock_post, mock_get_property_address):
        search_query = "PL2%201AD/ALBERT%20ROAD_10_FLAT%202"
        response = self.app.get('/properties/{}'.format(search_query))

        self.assertIn('"amount": "100001"', str(response.data))
        self.assertIn('"date": "2003-04-18"', str(response.data))

    @mock.patch('service.server.get_property_address', return_value=multiple_elastic_search_result.hits)
    def test_get_property_returns_404_error_when_the_DB_returns_two_result(self, mock_get_property_address):
        search_query = "PL6%208RU/PATTINSON%20DRIVE_100"
        response = self.app.get('/properties/{}'.format(search_query))

        self.assertEqual(response.status_code, 404)

    @mock.patch('service.server.get_property_address', return_value=single_elastic_search_result.hits)
    @mock.patch('requests.post', return_value=empty_PPI_response)
    def test_get_property_returns_no_PPI_data_when_PPI_API_returns_empty_result(self, mock_post, mock_get_property_address):
        search_query = "PL2%201AD/ALBERT%20ROAD_10_FLAT%202"
        response = self.app.get('/properties/{}'.format(search_query))

        self.assertIn('"amount": null', str(response.data))
        self.assertIn('"date": null', str(response.data))
        self.assertIn('"property_type": null', str(response.data))
