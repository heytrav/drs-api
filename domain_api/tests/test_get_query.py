from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from domain_api.epp.queries import EppRpcClient
import domain_api
import json
from ..exceptions import EppError

class MockRpcClient(domain_api.epp.queries.EppRpcClient):
    def __init__(self, host=None):
        pass

class TestCheckDomain(TestCase):

    def setUp(self):
        """
        Set up test suite
        :returns: TODO

        """
        self.client = Client()
        self.user = User.objects.create_user(
            username="testcustomer",
            email="testcustomer@test.com",
            password="secret"
        )

    def login_client(self):
        """
        Log user in to API.

        :returns: logged in session
        """
        self.client.login(username="testcustomer", password="secret")


    @patch('domain_api.epp.queries.EppRpcClient', new=MockRpcClient)
    def test_epp_error(self):
        """
        An epp error should result in a 400 bad request.
        """
        self.login_client()

        with patch.object(EppRpcClient, 'call', side_effect=EppError("FAIL")):
            response = self.client.get(
                '/domain-api/check-domain/test-registry/whatever.tld/'
            )
            self.assertEqual(response.status_code,
                             400,
                             "EPP error caused a 400 bad request.")

    @patch('domain_api.epp.queries.EppRpcClient', new=MockRpcClient)
    def test_check_domain_response(self):
        """
        EPP result returns serialized json response.
        """
        self.login_client()
        return_data = {
            "domain:chkData":{
                "domain:cd": {
                    "domain:name": {
                        "avail": 1
                    }
                }
            }
        }
        with patch.object(EppRpcClient, 'call', return_value=return_data):
            response = self.client.get(
                '/domain-api/check-domain/test-registry/whatever.tld/'
            )
            self.assertEqual(response.status_code,
                             200,
                             "Epp returned normally")
            data = json.loads(response.content)
            self.assertTrue(data["result"][0]["available"],
                            "Serialised a check_domain response")
