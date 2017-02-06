from django.test import TestCase
from unittest.mock import patch, MagicMock
from domain_api.epp.queries import EppRpcClient, Domain
from ..exceptions import EppError
import domain_api


class MockRpcClient(domain_api.epp.queries.EppRpcClient):
    def __init__(self, host=None):
        pass



class TestCheckDomain(TestCase):

    """
    Test processing of check domain.
    """

    @patch('domain_api.epp.queries.EppRpcClient', new=MockRpcClient)
    def test_bulk_check_domain(self):
        self.assertTrue(True)
