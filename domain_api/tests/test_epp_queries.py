from django.contrib.auth.models import User
from django.test import TestCase
from unittest.mock import patch
from domain_api.epp.queries import (
    ContactQuery,
    HostQuery
)
from domain_api.epp.entity import EppRpcClient
from domain_api.models import (
    Contact,
    DomainProvider,
    AccountDetail,
    TopLevelDomainProvider,
    TopLevelDomain,
)
import domain_api
from .test_setup import TestSetup


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestInfoContact(TestSetup):

    """
    Test processing info contact.
    """

    def setUp(self):
        super().setUp()

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_info_domain(self):
        """
        Test info domain processing.
        """
        info_contact_response = {
            "contact:infData": {
                "contact:authInfo": {
                    "contact:pw": "iafbv5yoe5cg4k8cww44kk0400wg8gg"
                },
                "contact:clID": "H93060719",
                "contact:crDate": "2017-01-23T02:48:25.0Z",
                "contact:crID": "H93060719",
                "contact:disclose": {
                    "contact:addr": {
                        "type": "int"
                    },
                    "contact:email": {},
                    "contact:fax": {},
                    "contact:name": {
                        "type": "int"
                    },
                    "contact:org": {
                        "type": "int"
                    },
                    "contact:voice": {},
                    "flag": "1"
                },
                "contact:email": "admin@test.com",
                "contact:fax": {},
                "contact:id": "reg-20",
                "contact:postalInfo": {
                    "contact:addr": {
                        "contact:cc": "US",
                        "contact:city": "Boston",
                        "contact:pc": "23433",
                        "contact:sp": "MA",
                        "contact:street": "Paralala Street"
                    },
                    "contact:name": "Joe User",
                    "contact:org": {},
                    "type": "int"
                },
                "contact:roid": "C112983065-CNIC",
                "contact:status": {
                    "s": "ok"
                },
                "contact:upDate": "2017-02-09T10:11:31.0Z",
                "contact:voice": "+64.11223344",
                "xmlns:contact": "urn:ietf:params:xml:ns:contact-1.0"
            }
        }
        contact_query = ContactQuery(
            Contact.objects.filter(project_id=self.user)
        )
        with patch.object(EppRpcClient,
                          'call',
                          return_value=info_contact_response):
            contact = Contact.objects.get(registry_id='contact-123')
            info_data = contact_query.info(contact)
            self.assertEqual("admin@test.com",
                             info_data.email,
                             "Response from info request contains email")
            self.assertEqual("reg-20",
                             info_data.registry_id,
                             "contact id is expected value")
            self.assertEqual(info_data.country, "US", "Expected country US")


class TestNameserver(TestSetup):

    """
    Test processing Nameserver queries/management
    """

    def setUp(self):
        """
        Setup test suite

        """

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_check_host_query(self):
        """
        Test processing check_host response

        """
        check_host_response = {
            "host:chkData": {
                "host:cd":  {
                    "host:name": {
                        "$t": "ns1.whatever.ote",
                        "avail": 1
                    }
                }
            }
        }
        # Shouldn't need a queryset yet
        host_query = HostQuery()
        with patch.object(EppRpcClient,
                          'call',
                          return_value=check_host_response):
            processed = host_query.check_host('ns1.whatever.ote')
            results = processed["result"]
            self.assertTrue(results[0]["available"],
                            "Processed response from check host command")
