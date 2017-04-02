from django.test import TestCase
from unittest.mock import patch
from domain_api.epp.actions.contact import Contact
from domain_api.epp.entity import EppRpcClient
import re
import domain_api


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestCreateContact(TestCase):

    def setUp(self):
        """
        Set up test suite.
        """
        super().setUp()

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_create_contact_succes(self):
        """
        Test processing of standard response from a create contact command.
        :returns: TODO

        """
        create_contact_response = {
            "contact:creData": {
                "contact:id": "A12345",
                "contact:crDate": "2017-02-10T00:00:00.0Z"
            }
        }
        contact = Contact()
        with patch.object(EppRpcClient,
                          'call',
                          return_value=create_contact_response):
            contact_data = {
                "id": 'A1234',
                "voice": '+1.12345678',
                "fax": "+1.1234589",
                "email": 'test@tester.com',
                "postalInfo": {
                    "name": "Joe Tester",
                    "org": "some company",
                    "type": "int",
                    "addr": {
                        "street": ["25", "whatever street"],
                        "city": "Springfield",
                        "sp": "State",
                        "pc": "123456",
                        "cc": "US"
                    }
                }
            }
            response_data = contact.create('test-registry', contact_data)
            self.assertIn('id', response_data)
            self.assertRegex(response_data["create_date"],
                             re.compile(r'\d{4}-\d{2}-\d{2}'),
                             "Contact has a create date.")
