from django.test import TestCase
from ..models import TopLevelDomain, TopLevelDomainProvider, DomainProvider
from ..entity_management.domains import DomainManagerFactory, CentralNic
from ..exceptions import UnsupportedTld, InvalidTld


class TestDomainManager(TestCase):

    """
    Test domain management stuff.
    """

    def setUp(self):
        """
        Set up test suite.
        """
        super().setUp()
        centralnic_test = DomainProvider(
            name="Provider1",
            slug="centralnic-test",
            description="Provide some domains"
        )
        centralnic_test.save()
        provider2 = DomainProvider(
            name="Provider2",
            slug="provider2",
            description="Provide some other domains"
        )
        provider2.save()
        tld = TopLevelDomain(
            zone="tld",
            idn_zone="tld",
            description="Test TLD"
        )
        tld.save()
        other_tld = TopLevelDomain(
            zone="other",
            idn_zone="other",
            description="Other Test TLD"
        )
        other_tld.save()
        tld_centralnic_test = TopLevelDomainProvider(
            zone=tld,
            provider=centralnic_test,
            anniversary_notification_period_days=10
        )
        tld_centralnic_test.save()
        self.factory = DomainManagerFactory()

    def test_fetch_expected_manager(self):
        """
        Request for domains with a specific tld should return a manager
        that can handle the tld.
        """
        manager = self.factory.get_manager("somedomain.tld")
        self.assertIsInstance(manager, CentralNic)
        manager2 = self.factory.get_manager("some.other.tld")
        self.assertIsInstance(manager2, CentralNic)

    def test_invalid_tld(self):
        """
        Should throw an invalid tld exception when tld does not exist.
        """
        with self.assertRaises(InvalidTld):
            self.factory.get_manager("tld-doesnot.exist")

    def test_unsupported_tld(self):
        """
        Should throw an unsupported tld error when there is no provider for a
        tld.
        """
        with self.assertRaises(UnsupportedTld):
            self.factory.get_manager("tld-provider.other")
