from unittest.mock import patch
from .test_setup import TestSetup
from ..epp.entity import EppRpcClient
import domain_api
import json


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestBasicQueries(TestSetup):

    def test_unauthenticated_endpoint_denied(self):
        """
        Test accessing an endpoint without JWT is denied.

        """
        response = self.client.get('/v1/account-detail/1/')
        self.assertEqual(response.status_code,
                         403,
                         "Not allowed to access endoint without JWT")

    def test_authenticateded_endpoint_accepted(self):
        """
        Test accessing an endpoint with JWT is allowed.

        """
        jwt_header = self.api_login()
        response = self.client.get('/v1/account-detail/1/',
                                   HTTP_AUTHORIZATION=jwt_header)
        self.assertEqual(response.status_code,
                         200,
                         "Allwed to request endpoint with JWT.")

    def test_unauthorized_endpoint_denied(self):
        """
        Test access to admin level object denied.
        """
        jwt_header = self.api_login()
        response = self.client.get('/v1/tld-provider/',
                                   HTTP_AUTHORIZATION=jwt_header)
        self.assertEqual(response.status_code,
                         403,
                         "Normal logged in user cannot  access tld-provider")

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_check_domain_response(self):
        """
        Check domain using JWT to authenticate

        """
        jwt_header = self.api_login()
        return_data = {
            "domain:chkData": {
                "domain:cd": {
                    "domain:name": {
                        "avail": 1,
                        "$t": "whatever.tld"
                    }
                }
            }
        }
        with patch.object(EppRpcClient, 'call', return_value=return_data):
            response = self.client.get(
                '/v1/domains/available/whatever.tld/',
                HTTP_AUTHORIZATION=jwt_header
            )
            self.assertEqual(response.status_code,
                             200,
                             "Epp returned normally")
            data = response.data
            self.assertTrue(data["available"],
                            "Serialised a check_domain response")


class TestHostApi(TestSetup):

    """
    Test api interaction to manage host objects
    """

    def setUp(self):
        """
        Setup test suite

        """
        super().setUp()

    def test_create_incorrect_data(self):
        """
        Should get an error when incorrectly structured host request sent to
        api.

        """
        bad_create_host = {
            "host": "ns1.somehost.com",
            "addr": [
                {"ip_addr": "23.34.45.67"},
            ]
        }
        jwt_header = self.api_login()
        response = self.client.post('/v1/hosts/',
                                    data=json.dumps(bad_create_host),
                                    content_type="application/json",
                                    HTTP_AUTHORIZATION=jwt_header)
        self.assertEqual(response.status_code,
                         400,
                         "incorrect create host datastructure returns 400")
        self.assertEqual('This field is required.',
                         response.data['addr']['ip'][0],
                         "ip field is required")
