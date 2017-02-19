from django.test import TestCase
from ..models import TopLevelDomain, TopLevelDomainProvider, DomainProvider
from ..exceptions import InvalidTld
from ..utilities.domain import parse_domain


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
