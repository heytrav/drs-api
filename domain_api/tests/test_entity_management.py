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
    def test_create_contact_payload(self):
        registrant_factory = RegistrantManager(
            provider=self.centralnic_test,
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
            mocked.assert_called_with('centralnic-test', actual_data)
            self.assertEqual(self.joe_user.id,
                             registrant.account_template.id,
                             'Account template is equal')

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_update_postal_data(self):
        registrant_factory = RegistrantManager(contact="registrant-123")
        update_return_value = {}
        update_contact_data = {
            "name": "Joe Luser",
            "city": "Shelbeyville",
            "state": "Flyover",
            "telephone": "+1.8172221233",
            "disclose_email": True,
            "status": "ok;clientHappy;linked"
        }

        with patch.object(ContactAction,
                          'update',
                          return_value=update_return_value) as mocked:
            registrant_factory.update_contact(update_contact_data)

            actual_data = {
                'id': "registrant-123",
                'add': ['clientHappy'],
                'chg': {
                    'postalInfo': {
                        'name': 'Joe Luser',
                        'type': 'loc',
                        'addr': {
                            'city': 'Shelbeyville',
                            'sp': 'Flyover',
                            'cc': 'US'
                        }
                    },
                    'voice':  '+1.8172221233',
                    'disclose': {
                        'flag': 1,
                        'disclosing': [
                            'email'
                        ]
                    }
                },
                'add': ['clientHappy', 'linked']
            }
            mocked.assert_called_with('centralnic-test', actual_data)


class TestDomainManager(TestSetup):
    """
    Test domain management stuff.
    """

    def test_parse_domain_components(self):
        """
        Request for domains with a specific tld should return a manager
        that can handle the tld.
        """
        parsed_domain = parse_domain("somedomain.ote")
        self.assertEqual(parsed_domain["domain"], "somedomain")
        self.assertEqual(parsed_domain["zone"], "ote")
        parsed_domain = parse_domain("some.other.ote")
        self.assertEqual(parsed_domain["domain"], "other")
        self.assertEqual(parsed_domain["zone"], "ote")

    def test_invalid_tld(self):
        """
        Should throw an invalid tld exception when tld does not exist.
        """
        with self.assertRaises(InvalidTld):
            parse_domain("tld-doesnot.exist")
