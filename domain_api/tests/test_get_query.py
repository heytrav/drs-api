from unittest.mock import patch
from domain_api.epp.entity import EppRpcClient
import domain_api
import json
from ..exceptions import EppError

from .test_api_interaction import TestApiClient


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestCheckDomain(TestApiClient):

    def setUp(self):
        """
        Set up test suite

        """
        super().setUp()

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_epp_error(self):
        """
        An epp error should result in a 400 bad request.
        """
        self.login_client()

        with patch.object(EppRpcClient, 'call', side_effect=EppError("FAIL")):
            response = self.client.get(
                '/v1/check-domain/test-registry/whatever.tld/'
            )
            self.assertEqual(response.status_code,
                             400,
                             "EPP error caused a 400 bad request.")

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_check_domain_response(self):
        """
        EPP check domain result returns serialized json response.
        """
        self.login_client()
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
                '/v1/check-domain/test-registry/whatever.tld/'
            )
            self.assertEqual(response.status_code,
                             200,
                             "Epp returned normally")
            data = json.loads(response.content.decode('utf-8'))
            self.assertTrue(data["result"][0]["available"],
                            "Serialised a check_domain response")


class TestInfoDomain(TestApiClient):

    """
    Test info domain functionality
    """
    def setUp(self):
        """
        Set up test suite
        """
        super().setUp()

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_info_domain_response(self):
        """
        Test processing of info domain response
        """
        self.login_client()
        return_value = {
            "domain:infData": {
                "domain:name": "whatever.tld",
                "domain:status": "ok",
                "domain:registrant": "R1234",
                "domain:ns": [
                    {
                        "domain:hostObj": "ns1.nameserver.com"
                    },
                    {
                        "domain:hostObj": "ns2.nameserver.com"
                    }
                ],
                "domain:contact": [
                    {
                        "$t": "A1234",
                        "type": "admin",
                    },
                    {
                        "$t": "T1234",
                        "type": "tech",
                    }
                ]
            }
        }
        with patch.object(EppRpcClient, 'call', return_value=return_value):
            response = self.client.get(
                '/v1/info-domain/test-registry/whatever.tld/'
            )
            self.assertEqual(response.status_code,
                             200,
                             "Epp returned normally")
