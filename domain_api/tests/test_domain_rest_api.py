from unittest.mock import patch
import json
from ..workflows import CentralNic
from .test_setup import TestSetup


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
        self.client.post('/v1/domains/',
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
        self.client.post('/v1/domains/',
                         data=json.dumps(create_domain_data),
                         content_type='application/json',
                         HTTP_AUTHORIZATION=jwt_header)
        self.assertEqual(3,
                         len(mock_append.mock_calls),
                         "Expected number of calls to append")

    @patch.object(CentralNic, 'append')
    @patch.object(CentralNic, 'append_contacts_to_epp')
    def test_assert_create_domain_workflow_prefills_epp(self,
                                                        mock_append_epp,
                                                        mock_append):
        """
        Test that the append function is called a expected number of times.
        """
        create_domain_data = {
            "domain": "test-new-domain.xyz",
        }
        jwt_header = self.api_login()
        self.client.post('/v1/domains/',
                         data=json.dumps(create_domain_data),
                         content_type='application/json',
                         HTTP_AUTHORIZATION=jwt_header)
        mock_append_epp.assert_called_with(
            {
                "name": "test-new-domain.xyz",
                "registrant": "registrant-123",
            },
            [{"admin": "contact-123"}, {"tech": "contact-321"}]
        )

        self.assertEqual(3, len(mock_append.mock_calls),
                         "Assert appends() called a few times")
