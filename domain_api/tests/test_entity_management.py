from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, ANY
from ..exceptions import InvalidTld
from ..utilities.domain import parse_domain
from ..entity_management.contacts import (
    RegistrantManager,
    ContactManager,
    ContactAction
)
from ..models import (
    AccountDetail,
    DomainProvider,
    TopLevelDomain,
    TopLevelDomainProvider,
    DefaultAccountContact,
    ContactType,
    Contact
)
import domain_api


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestEntityManager(TestCase):
    def setUp(self):
        super().setUp()
        self.centralnic_test = DomainProvider.objects.create(
            name="Provider1",
            slug="centralnic-test",
            description="Provide some domains"
        )
        self.provider = DomainProvider.objects.create(
            name="Provider One",
            slug="provider-one",
            description="Provide some domains"
        )
        self.provider2 = DomainProvider.objects.create(
            name="Provider2",
            slug="provider2",
            description="Provide some other domains"
        )
        tld = TopLevelDomain(
            zone="tld",
            description="Test TLD"
        )
        tld.save()
        other_tld = TopLevelDomain(
            zone="other",
            description="Other Test TLD"
        )
        other_tld.save()
        tld_centralnic_test = TopLevelDomainProvider(
            zone=tld,
            provider=self.centralnic_test,
            expiration_notification_period_days=10
        )
        tld_centralnic_test.save()
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
            postal_info_type="loc",
            disclose_name=False,
            disclose_telephone=False,
            project_id=self.user
        )


class TestContactManager(TestEntityManager):
    """
    Test contact management stuff.
    """

    def setUp(self):
        """
        Set up test suite.
        """
        super().setUp()

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_contact_payload(self):
        registrant_factory = RegistrantManager(
            provider=self.provider,
            template=self.joe_user,
            user=self.user
        )
        create_return_value = {
            "id": "A1234",
            "create_date": "2017-03-01T12:00:00Z"
        }

        with patch.object(ContactAction, 'create', return_value=create_return_value) as mocked:
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
                        { 'name': 'name', 'type': 'loc'},
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


class TestDomainManager(TestEntityManager):

    """
    Test domain management stuff.
    """

    def setUp(self):
        """
        Set up test suite.
        """
        super().setUp()

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
