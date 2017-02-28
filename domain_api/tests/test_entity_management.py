from django.test import TestCase
from unittest import patch, MockObject
from ..exceptions import InvalidTld
from ..utilities.domain import parse_domain
from ..entity_management.contacts import (
    ContactManager,
    RegistrantManager,
    ContactAction
)
from ..models import (
    PersonalDetail,
    DomainProvider,
    Contact,
    TopLevelDomain,
    TopLevelDomainProvider,
    Registrant
)
import domain_api



class TestEntityManager(TestCase):
    def setUp():
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

    @patch('domain_api.entity_management.contacts.ContactAction', new=MockObject)
    def test_contact_payload(self):
        registrant_factory = RegistrantManager(
            provider=self.provider,
            person=self.joe_user
        )




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
