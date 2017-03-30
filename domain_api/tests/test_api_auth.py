from unittest.mock import patch
from .test_api_interaction import TestApiClient
from ..epp.entity import EppRpcClient
import domain_api


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestBasicQueries(TestAPIAuth):

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
