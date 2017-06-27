from unittest.mock import patch
import json
import domain_api
from ..workflows import CentralNic
from domain_api.epp.entity import EppRpcClient
from .test_setup import TestSetup


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestDomainApi(TestSetup):

    def setUp(self):
        """
        Set up test suite
        :returns: TODO

        """
        super().setUp()
        self.create_domain_response = {
            "domain:creData": {
                "xmlns:domain": "urn:ietf:params:xml:ns:domain-1.0",
                "domain:name": "test-new-domain.xyz",
                "domain:crDate": "2017-06-26T20:50:08.0Z",
                "domain:exDate": "2018-06-26T23:59:59.0Z"
            }
        }

    @patch.object(CentralNic, 'create_domain')
    def test_create_new_domain(self, mock_create_domain):
        """
        Test create domain using ModelViewSet

        """
        create_domain_data = {
            "domain": "test-new-domain.xyz",
            "nameservers": ["ns1.nameserver.com", "ns2.nameserver.com"]
        }
        jwt_header = self.api_login()
        self.client.post('/v1/registered-domains/',
                         data=json.dumps(create_domain_data),
                         content_type='application/json',
                         HTTP_AUTHORIZATION=jwt_header)
        mock_create_domain.assert_called_with(create_domain_data,
                                              self.test_customer_user)

    @patch.object(CentralNic, 'append')
    def test_assert_create_domain_workflow_appends(self, mock_append):
        """
        Test that the append function is called a expected number of times.
        """
        create_domain_data = {
            "domain": "test-new-domain.xyz",
            "nameservers": ["ns1.nameserver.com", "ns2.nameserver.com"]
        }
        jwt_header = self.api_login()
        self.client.post('/v1/registered-domains/',
                         data=json.dumps(create_domain_data),
                         content_type='application/json',
                         HTTP_AUTHORIZATION=jwt_header)
        self.assertEqual(6,
                         len(mock_append.mock_calls),
                         "Expected number of calls to append")
