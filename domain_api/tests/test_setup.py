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

    fixtures = ["test_auth.json", "contact_types.json",
                "providers.json",
                "tlds.json",
                "tld_providers.json",
                "test_account_details.json",
                "default_account_contacts.json",
                "test_contacts.json",
                "test_registrants.json"]

    """
    Set up users, providers, tlds, etc. for testing.
    """

    def setUp(self):
        """
        Set up test suite
        """
        super().setUp()
        self.client = Client()
        self.user = User.objects.get(username='testadmin')
        self.test_customer_user = User.objects.get(username='testcustomer')
        self.joe_user = self.test_customer_user.personal_details.filter(
            email='joeuser@test.com'
        ).first()
        self.joe_user_registrant = self.test_customer_user.registrants.filter(
            email='joeuser@test.com'
        ).first()
        self.centralnic_test = DomainProvider.objects.get(slug="centralnic-test")
        self.generic_admin_contact = Contact.objects.get(
            registry_id="contact-123"
        )


    def api_login(self,
                  username="testcustomer",
                  password="imacust1"):
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
        self.client.login(username="testcustomer", password="imacust1")
