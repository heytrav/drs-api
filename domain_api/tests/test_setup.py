from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from ..models import (
    TopLevelDomain,
    TopLevelDomainProvider,
    DomainProvider,
    AccountDetail,
    DefaultAccountTemplate,
    Registrant,
    ContactType,
    DefaultAccountContact,
    Contact,
)


class TestSetup(TestCase):

    """
    Set up users, providers, tlds, etc. for testing.
    """

    def setUp(self):
        """
        Set up test suite
        """
        super().setUp()
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="secret"
        )
        Group.objects.create(name='customer')
        Group.objects.create(name='admin')
        self.test_customer_user = User.objects.create_user(
            username="testcustomer",
            email="testcustomer@test.com",
            password="secret"
        )
        self.test_customer_user2 = User.objects.create_user(
            username="testcustomer2",
            email="testcustomer2@test.com",
            password="secret2"
        )
        self.centralnic_test = DomainProvider.objects.create(
            name="Provider1",
            slug="centralnic-test",
            description="Provide some domains"
        )
        self.provider_one = DomainProvider.objects.create(
            name="Provider One",
            slug="provider-one",
            description="Provide some domains"
        )
        self.provider_two = DomainProvider.objects.create(
            name="Provider2",
            slug="provider2",
            description="Provide some other domains"
        )
        self.tld = TopLevelDomain.objects.create(
            zone="tld",
            description="Test TLD"
        )
        self.tld_provider = TopLevelDomainProvider.objects.create(
            zone=self.tld,
            provider=self.provider_one,
            expiration_notification_period_days=30
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
            project_id=self.test_customer_user
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
            project_id=self.test_customer_user
        )
        self.other_user = AccountDetail.objects.create(
            first_name="Other",
            surname="User",
            email="otheruser@test.com",
            telephone="+1.8175551234",
            house_number="10",
            street1="Evergreen Terrace",
            city="Springfield",
            state="State",
            country="US",
            postal_info_type="loc",
            disclose_name=False,
            disclose_telephone=False,
            project_id=self.test_customer_user2
        )
        self.default_registrant = DefaultAccountTemplate.objects.create(
            project_id=self.test_customer_user,
            account_template=self.joe_user,
            provider=self.provider_one
        )
        self.joe_user_registrant = Registrant.objects.create(
            registry_id='registrant-123',
            project_id=self.test_customer_user,
            provider=self.provider_one,
            account_template=self.joe_user
        )
        self.bob_user_registrant = Registrant.objects.create(
            provider=self.provider_one,
            registry_id='registrant-231',
            name='Bob User',
            project_id=self.test_customer_user,
            account_template=self.bob_user
        )
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
            provider=self.provider_one,
            contact_type=admin_type,
        )
        self.default_tech = DefaultAccountContact.objects.create(
            project_id=self.admin_user,
            account_template=self.tech_acct1,
            provider=self.provider_one,
            contact_type=tech_type,
        )
        self.generic_admin_contact = Contact.objects.create(
            provider=self.provider_one,
            registry_id='contact-123',
            name='Some Admin',
            project_id=self.admin_user,
            account_template=self.admin_acct1
        )
        self.other_user_contact2 = Contact.objects.create(
            registry_id='contact-124',
            project_id=self.test_customer_user2,
            provider=self.provider_one,
            account_template=self.other_user
        )

    def api_login(self,
                  username="testcustomer",
                  password="secret"):
        """
        Log client in using api-token-auth endpoint
        :returns: str JSON Web token
        """
        credentials = {
            "username": username,
            "password": password
        }
        response = self.client.post('/api-token-auth',
                                    secure=True,
                                    data=credentials)
        data = response.data
        return 'JWT ' + data["token"]

    def login_client(self):
        """
        Log user in to API.

        :returns: logged in session
        """
        self.client.login(username="testcustomer", password="secret")
