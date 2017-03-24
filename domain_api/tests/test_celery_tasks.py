from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch
from ..tasks import (
    check_domain,
    create_registrant,
    create_registry_contact,
    ContactManager,
    RegistrantManager
)
from ..exceptions import EppError
from domain_api.epp.entity import EppRpcClient
from ..models import (
    AccountDetail,
    DomainProvider,
    Contact,
    TopLevelDomain,
    TopLevelDomainProvider,
    Registrant,
    ContactType,
    DefaultAccountContact,
    DefaultAccountTemplate
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
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="secret"
        )
        self.user = User.objects.create_user(
            username="testcustomer",
            email="testcustomer@test.com",
            password="secret"
        )
        self.joe_user = AccountDetail.objects.create(
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
        self.bob_user = AccountDetail.objects.create(
            first_name="bob",
            surname="User",
            email="bobuser@test.com",
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
        self.default_registrant = DefaultAccountTemplate.objects.create(
            project_id=self.user,
            account_template=self.joe_user,
            provider=self.provider
        )
        self.generic_registrant = Registrant.objects.create(
            provider=self.provider,
            registry_id='registrant-231',
            name='Bob User',
            project_id=self.user,
            account_template=self.bob_user
        )

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
                                              self.user.id)
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
                                  self.user.id)

    def test_must_create_new_registrant(self):
        """
        Test that we must create a new registrant.

        """
        with patch.object(RegistrantManager,
                          'create_registry_contact',
                          return_value=self.generic_registrant) as mocked:
            create_registrant({},
                              self.joe_user.id,
                              'provider-one',
                              self.user.id)
            self.assertTrue(mocked.called)


class TestCreateContact(ContactOperation):

    """
    Test creation of a regsitrant object.
    """

    def setUp(self):
        super().setUp()
        self.admin_acct1 = AccountDetail.objects.create(
            first_name="Ada",
            surname="min",
            email="admin@test.com",
            telephone="+1.8175551234",
            house_number="10",
            street1="Evergreen Terrace",
            city="Springfield",
            state="State",
            country="US",
            postal_info_type="loc",
            project_id=self.admin_user
        )
        self.tech_acct1 = AccountDetail.objects.create(
            first_name="Tech",
            surname="Guy",
            email="tech@test.com",
            telephone="+1.8175551234",
            house_number="10",
            street1="Evergreen Terrace",
            city="Springfield",
            state="State",
            country="US",
            postal_info_type="loc",
            disclose_name=False,
            disclose_telephone=False,
            project_id=self.admin_user
        )
        admin_type = ContactType.objects.create(name='admin',
                                                description='Admin contact')
        tech_type = ContactType.objects.create(name='tech',
                                               description='Admin contact')

        self.default_admin = DefaultAccountContact.objects.create(
            project_id=self.admin_user,
            account_template=self.admin_acct1,
            provider=self.provider,
            contact_type=admin_type,
        )
        self.default_tech = DefaultAccountContact.objects.create(
            project_id=self.admin_user,
            account_template=self.tech_acct1,
            provider=self.provider,
            contact_type=tech_type,
        )
        self.generic_admin_contact = Contact.objects.create(
            provider=self.provider,
            registry_id='contact-123',
            name='Some Admin',
            project_id=self.user,
            account_template=self.admin_acct1
        )

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
                                                    self.user.id)
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

    def test_must_create_new_registry_contact(self):
        """
        Test that we must create a new contact.

        """
        with patch.object(ContactManager,
                          'create_registry_contact',
                          return_value=self.generic_admin_contact) as mocked:
            create_registry_contact({},
                                    self.joe_user.id,
                                    'provider-one',
                                    'tech',
                                    self.user.id)
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
                                        'provider-one',
                                        'admin',
                                        self.user.id)


class TestConnectTask(TestCase):

    """Docstring for TestConnectTask. """

    def setUp(self):
        """
        Set up test suite
        :returns: TODO

        """
        super().setUp()
