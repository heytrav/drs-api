from unittest.mock import patch, ANY
from .test_setup import TestSetup
from ..exceptions import InvalidTld
from ..utilities.domain import parse_domain
from ..entity_management.contacts import (
    RegistrantManager,
    ContactAction
)
import domain_api


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestContactManager(TestSetup):
    """
    Test contact management stuff.
    """

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_contact_payload(self):
        registrant_factory = RegistrantManager(
            provider=self.provider_one,
            template=self.joe_user,
            user=self.test_customer_user
        )
        create_return_value = {
            "id": "A1234",
            "create_date": "2017-03-01T12:00:00Z"
        }

        with patch.object(ContactAction,
                          'create',
                          return_value=create_return_value) as mocked:
            registrant = registrant_factory.create_registry_contact()

            actual_data = {
                'id': ANY,
                'voice': '+1.8175551234',
                'fax': '',
                'email': 'joeuser@test.com',
                'postalInfo': {
                    'name': 'Joe User',
                    'org': '',
                    'type': 'loc',
                    'addr': {
                        'street': ['Evergreen Terrace'],
                        'city': 'Springfield',
                        'sp': 'State',
                        'pc': '',
                        'cc': 'US'}
                },
                'disclose': {
                    'flag': 0,
                    'disclosing': [
                        {'name': 'name', 'type': 'loc'},
                        {'name': 'org', 'type': 'loc'},
                        {'name': 'addr', 'type': 'loc'},
                        'voice', 'fax', 'email'
                    ]
                }
            }
            mocked.assert_called_with('provider-one', actual_data)
            self.assertEqual(self.joe_user.id,
                             registrant.account_template.id,
                             'Account template is equal')


class TestDomainManager(TestSetup):
    """
    Test domain management stuff.
    """

    def test_parse_domain_components(self):
        """
        Request for domains with a specific tld should return a manager
        that can handle the tld.
        """
        parsed_domain = parse_domain("somedomain.tld")
        self.assertEqual(parsed_domain["domain"], "somedomain")
        self.assertEqual(parsed_domain["zone"], "tld")
        parsed_domain = parse_domain("some.other.tld")
        self.assertEqual(parsed_domain["domain"], "other")
        self.assertEqual(parsed_domain["zone"], "tld")

    def test_invalid_tld(self):
        """
        Should throw an invalid tld exception when tld does not exist.
        """
        with self.assertRaises(InvalidTld):
            parse_domain("tld-doesnot.exist")
