from django.test import TestCase
from unittest.mock import patch, MagicMock
from domain_api.epp.queries import EppRpcClient
from ..exceptions import EppError


class MockRpcClient(domain_api.epp.queries.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestCheckDomain(TestCase):

    """
    Test processing of check domain.
    """
