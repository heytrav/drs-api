from unittest.mock import patch
from .test_setup import TestSetup
from ..tasks import (
    check_domain,
    create_registrant,
    create_registry_contact,
    ContactManager,
    RegistrantManager
)
from ..exceptions import EppError
from ..models import (
    Contact,
    Registrant,
)
from domain_api.epp.entity import EppRpcClient
import domain_api


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestCheckDomainTask(TestSetup):

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_domain_available(self):
        check_domain_response = {
            "domain:chkData": {
                "domain:cd": {
                    "domain:name": {
                        "$t": "somedomain.ote",
                        "avail": 1
                    }
                }
            }
        }
        with patch.object(EppRpcClient,
                          'call',
                          return_value=check_domain_response):
            available = check_domain("somedomain.ote")
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


class TestCreateRegistrant(TestSetup):

    """
    Test creation of a regsitrant object.
    """

    def setUp(self):
        super().setUp()
        self.new_registrant = self.test_customer_user.personal_details.filter(
            email='joeuser2@test.com'
        ).first()

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_create_registrant(self):
        """
        Check that registrant handle is added to DB
        """
        epp = {}
        create_contact_response = {
            "contact:creData": {
                "contact:id": "tk429",
                "contact:crDate": "2017-01-01T12:00:01"
            }
        }
        with patch.object(EppRpcClient,
                          'call',
                          return_value=create_contact_response):
            processed_epp = create_registrant(epp,
                                              self.new_registrant.id,
                                              'centralnic-test',
                                              self.test_customer_user.id)
            self.assertIn('registrant',
                          processed_epp,
                          "Registrant added to epp")
            self.assertEqual('tk429',
                             processed_epp['registrant'],
                             "Registrant had handle id.")
            contact = self.joe_user.user.registrants.filter(
                registry_id='tk429'
            ).first()
            self.assertIsInstance(contact,
                                  Registrant,
                                  'Created expected contact handle')

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_create_registrant_epp_error(self):
        """
        Check that an EPP error causes failure.
        """
        with patch.object(EppRpcClient,
                          'call',
                          side_effect=EppError("FAIL")):
            with self.assertRaises(EppError):
                create_registrant({},
                                  self.new_registrant.id,
                                  'centralnic-test',
                                  self.test_customer_user.id)

    def test_must_create_new_registrant(self):
        """
        Test that we must create a new registrant.

        """
        with patch.object(RegistrantManager,
                          'create_registry_contact',
                          return_value=self.joe_user_registrant) as mocked:
            create_registrant({},
                              self.new_registrant.id,
                              'centralnic-test',
                              self.test_customer_user.id)
            self.assertTrue(mocked.called)


class TestCreateContact(TestSetup):

    """
    Test creation of a regsitrant object.
    """

    def setUp(self):
        super().setUp()

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_create_contact(self):
        """
        Check that contact handle is added to DB
        """
        epp = {}
        create_contact_response = {
            "contact:creData": {
                "contact:id": "tk429",
                "contact:crDate": "2017-01-01T12:00:01"
            }
        }
        with patch.object(EppRpcClient,
                          'call',
                          return_value=create_contact_response):
            processed_epp = create_registry_contact(epp,
                                                    self.joe_user.id,
                                                    'centralnic-test',
                                                    'tech',
                                                    self.test_customer_user.id)
            self.assertIn('contact',
                          processed_epp,
                          "Contact added to epp")
            contact = processed_epp["contact"]
            self.assertIsInstance(contact, list)
            (contact_type, contact_id), = contact[0].items()

            self.assertEqual('tech',
                             contact_type,
                             "Added a tech contact to EPP")
            contact = self.joe_user.user.contacts.filter(
                registry_id='tk429'
            ).first()
            self.assertIsInstance(contact,
                                  Contact,
                                  'Created expected contact handle')

    def test_must_create_new_registry_contact(self):
        """
        Test that we must create a new contact.

        """
        with patch.object(ContactManager,
                          'create_registry_contact',
                          return_value=self.generic_admin_contact) as mocked:
            create_registry_contact({},
                                    self.joe_user.id,
                                    'centralnic-test',
                                    'tech',
                                    self.test_customer_user.id)
            self.assertTrue(mocked.called)

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_create_contact_epp_error(self):
        """
        Check that an EPP error causes failure.
        """
        with patch.object(EppRpcClient,
                          'call',
                          side_effect=EppError("FAIL")):
            with self.assertRaises(EppError):
                create_registry_contact({},
                                        self.joe_user.id,
                                        'centralnic-test',
                                        'admin',
                                        self.test_customer_user.id)
