from service.server import app, get_query_parts
import mock
import unittest
import requests
import responses



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

    @mock.patch('requests.post', returns=search_results)
    def test_search_results_calls_search_api(self, mock_post):
        search_query = "PL6%208RU/PATTINSON%20DRIVE_100"

        query_dict = {
            'postcode': 'PL6 8RU',
            'street': 'ATTINSON DRIVE',
            'paon': '100',
        }

        query = '\nprefix xsd: <http://www.w3.org/2001/XMLSchema#>\nprefix lrppi: <http://landregistry.data.gov.uk/def/ppi/>\nprefix lrcommon: <http://landregistry.data.gov.uk/def/common/>\n\n# Returns the Price Paid data from the default graph for each transaction record having\n# an address with the given postcode.\n# The postcode to query is set in the line - ?address_instance common:postcode "PL6 8RU"^^xsd:string .\n\n\nSELECT ?amount ?date ?property_type\nWHERE\n{\n    ?transx lrppi:pricePaid ?amount ;\n            lrppi:transactionDate ?date ;\n            lrppi:propertyAddress ?addr ;\n            lrppi:propertyType ?property_type.\n  ?addr lrcommon:street "PATTINSON DRIVE"^^xsd:string.\n  ?addr lrcommon:postcode "PL6 8RU"^^xsd:string.\n  ?addr lrcommon:paon "100"^^xsd:string.\n\n}\nORDER BY desc(?date) limit 1\n'

        response = self.app.get('/properties/%s' % search_query)
        mock_post.assert_called_with('%s' % (self.ppi_api), data={'output': 'json', 'query': query})


'''
    @mock.patch('requests.get', returns=search_results)
    def test_search_results_calls_search_api(self, mock_get):
        search_query = "TN12"
        response = self.app.get('/search/results?search=%s' % search_query)
        mock_get.assert_called_with('%s/search?query=%s' % (self.search_api, search_query))

    @mock.patch('requests.get')
    @mock.patch('requests.Response')
    def test_get_property_preserves_downstream_500(self, mock_response, mock_get):
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
        mock_get.return_value = mock_response
        search_query = "TN12"
        response = self.app.get('/search/results?search=%s' % search_query)
        assert response.status_code == 500

    @mock.patch('requests.get', side_effect=requests.exceptions.ConnectionError)
    def test_requests_connection_error_results_in_500(self, mock_get):
        search_query = "TN12"
        response = self.app.get('/search/results?search=%s' % search_query)
        assert response.status_code == 500

    @mock.patch('requests.get')
    @mock.patch('requests.Response')
    def test_for_service_frontend_link(self, mock_response, mock_get):
      mock_response.status_code = 200
      mock_response.json.return_value = title
      mock_get.return_value = mock_response
      title_number = "TN1234567"
      rv = self.app.get('/property/%s' % title_number)
      service_frontend_url = '%s/%s/%s' % (self.service_api, 'property', title_number)
      assert service_frontend_url in rv.data

    @responses.activate
    def test_for_two_search_results(self):
        #Mock a response, as though JSON is coming back from SEARCH_API
        TITLE_NUMBER = "TN1234567"
        search_api_url = "%s/%s" % (self.search_api, "search")
        search_url = "%s?query=%s" % (search_api_url, TITLE_NUMBER)
        app.logger.info(search_url)

        #match_querystring essential when a query specified.
        #default value of match_querystring is false.  Relies on query being absent.
        responses.add(responses.GET, search_url, match_querystring = True,
        body = test_two_search_results, status = 200, content_type='application/json')

        rv = self.app.get('search/results?search=%s' % TITLE_NUMBER,
          follow_redirects=True)
        app.logger.info(rv.data)

        self.assertEquals(rv.status_code, 200)
        self.assertTrue("TN1234567" in rv.data)
        self.assertTrue("8 Miller Way"  in rv.data)
        self.assertTrue("PL6 8UQ" in rv.data)
        self.assertTrue("Plymouth" in rv.data)
        self.assertTrue("Devon" in rv.data)
        self.assertTrue("TN7654321" in rv.data)
        self.assertTrue("10 Low St" in rv.data)


    def health(self):
        response = self.app.get('/health')
        assert response.status == '200 OK'
'''
