from django.test import TestCase
from django.contrib.auth.models import User, Client
from ..models import (
    TopLevelDomain,
    TopLevelDomainProvider,
    DomainProvider,
    AccountDetail
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
        self.user = User.objects.create_user(
            username="testcustomer",
            email="testcustomer@test.com",
            password="secret"
        )
        self.user2 = User.objects.create_user(
            username="testcustomer2",
            email="testcustomer2@test.com",
            password="secret2"
        )
        test_registry = DomainProvider(
            name="Provider1",
            slug="test-registry",
            description="Provide some domains"
        )
        test_registry.save()
        self.provider = test_registry
        tld = TopLevelDomain(
            zone="tld",
            description="Test TLD"
        )
        tld.save()
        tld_provider = TopLevelDomainProvider(
            zone=tld,
            provider=test_registry,
            expiration_notification_period_days=30
        )
        tld_provider.save()
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
            project_id=self.user
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
            "password": secret
        }
        response = self.client.post('/api-token-auth',
                                    secure=True,
                                    data=credentials)
        data = response.data
        return 'JWT ' + data["token"]
