from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch
from ..tasks import check_domain, create_registrant, create_registry_contact
from ..exceptions import EppError
from domain_api.epp.entity import EppRpcClient
from ..models import (
    PersonalDetail,
    DomainProvider,
    Contact,
    TopLevelDomain,
    TopLevelDomainProvider,
    Registrant
)
import domain_api


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestCheckDomainTask(TestCase):

    def setUp(self):
        super().setUp()
        test_registry = DomainProvider(
            name="Provider1",
            slug="test-registry",
            description="Provide some domains"
        )
        test_registry.save()
        tld = TopLevelDomain(
            zone="tld",
            idn_zone="tld",
            description="Test TLD"
        )
        tld.save()
        tld_provider = TopLevelDomainProvider(
            zone=tld,
            provider=test_registry,
            anniversary_notification_period_days=30
        )
        tld_provider.save()

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
            available = check_domain("somedomain.tld")
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


class ContactOperation(TestCase):

    """
    Set up some basic stuff to handle a domain registration.
    """

    def setUp(self):
        super().setUp()
        self.provider = DomainProvider.objects.create(
            name="Provider One",
            slug="provider-one",
            description="Provide some domains"
        )
        self.user = User.objects.create_user(
            username="testcustomer",
            email="testcustomer@test.com",
            password="secret"
        )

        self.joe_user = PersonalDetail.objects.create(
            first_name="Joe",
            surname="User",
            email="joeuser@test.com",
            telephone="+1.8175551234",
            house_number="10",
            street1="Evergreen Terrace",
            city="Springfield",
            state="State",
            country="US",
            project_id=self.user
        )


class TestCreateRegistrant(ContactOperation):

    """
    Test creation of a regsitrant object.
    """

    def setUp(self):
        super().setUp()

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
                                              self.joe_user.id,
                                              'provider-one',
                                              self.user)
            self.assertIn('registrant',
                          processed_epp,
                          "Registrant added to epp")
            self.assertEqual('tk429',
                             processed_epp['registrant'],
                             "Registrant had handle id.")
            contact = self.joe_user.project_id.registrants.filter(
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
                                  self.joe_user.id,
                                  'provider-one',
                                  self.user)


class TestCreateContact(ContactOperation):

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
                                                    'provider-one',
                                                    'tech',
                                                    self.user)
            self.assertIn('contact',
                          processed_epp,
                          "Contact added to epp")
            contact = processed_epp["contact"]
            self.assertIsInstance(contact, list)
            (contact_type, contact_id), = contact[0].items()

            self.assertEqual('tech',
                             contact_type,
                             "Added a tech contact to EPP")
            contact = self.joe_user.project_id.contacts.filter(
                registry_id='tk429'
            ).first()
            self.assertIsInstance(contact,
                                  Contact,
                                  'Created expected contact handle')

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
                                        'provider-one',
                                        'admin',
                                        self.user)


class TestConnectTask(TestCase):

    """Docstring for TestConnectTask. """

    def setUp(self):
        """
        Set up test suite
        :returns: TODO

        """
        super().setUp()
