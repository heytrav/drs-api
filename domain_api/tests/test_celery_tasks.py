from django.test import TestCase
from unittest.mock import patch
from ..tasks import check_domain
from domain_api.epp.entity import EppRpcClient
import domain_api


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestCheckDomainTask(TestCase):

    def setUp(self):
        super().setUp()

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_domain_available(self):
        check_domain_response = {
            "domain:chkData": {
                "domain:cd": {
                    "domain:name": {
                        "$t": "somedomain.tld",
                        "avail": 1
                    }
                }
            }
        }
        with patch.object(EppRpcClient,
                          'call',
                          return_value=check_domain_response):
            available = check_domain("somedomain.tld", "test-registry")
            self.assertTrue(available, "Domain is available")

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_domain_unavailable(self):
        check_domain_response = {
            "domain:chkData": {
                "domain:cd": {
                    "domain:name": {
                        "$t": "somedomain.tld",
                        "avail": 0
                    }
                }
            }
        }
        with patch.object(EppRpcClient,
                          'call',
                          return_value=check_domain_response):
            with self.assertRaises(Exception):
                check_domain("somedomain.tld", "test-registry")


class TestConnectTask(TestCase):

    """Docstring for TestConnectTask. """

    def setUp(self):
        """
        Set up test suite
        :returns: TODO

        """
        super().setUp()
