from django.contrib.auth.models import User
from domain_api.views import DomainRegistryManagementViewSet
from domain_api.models import (
    RegisteredDomain,
    TopLevelDomainProvider,
)
from .test_setup import TestSetup


class MockRequest(object):

    def __init__(self):
        self.user = User.objects.get(pk=2)


class MockeDomainRegistryManagementViewSet(DomainRegistryManagementViewSet):

    def __init__(self):
        self.request = MockRequest()


class TestDomainViewMethods(TestSetup):

    def setUp(self):
        """
        Set up test suite
        """
        tld_provider = TopLevelDomainProvider.objects.filter(
            zone__zone='ote'
        ).first()
        tld = tld_provider.zone
        self.registered_domain = RegisteredDomain.objects.get(
            domain__name="test-domain",
            tld=tld,
            tld_provider=tld_provider,
            active=True,
            registration_period=1
        )

    def test_admin_check_domain_contacts(self):
        """
        Test bugfix for exception thrown in admin or owner check function
        """
        def call_code(view_obj, domain):
            print("Executing call code")
            try:
                view_obj.is_admin_or_owner(domain)
                return True
            except Exception as e:
                print("Code threw an exception" + str(e))
                return False

        view = MockeDomainRegistryManagementViewSet()
        result = call_code(view, self.registered_domain)
        self.assertTrue(result, "Request doesn't cause an exception")
