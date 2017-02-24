from django.test import TestCase, Client
from django.contrib.auth.models import User
from ..models import (
    TopLevelDomain,
    TopLevelDomainProvider,
    DomainProvider
)


class TestApiClient(TestCase):

    def setUp(self):
        """
        Set up test suite
        """
        self.client = Client()
        self.user = User.objects.create_user(
            username="testcustomer",
            email="testcustomer@test.com",
            password="secret"
        )
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

    def login_client(self):
        """
        Log user in to API.

        :returns: logged in session
        """
        self.client.login(username="testcustomer", password="secret")
