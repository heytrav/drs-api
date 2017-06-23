from unittest.mock import patch
from domain_api.epp.queries import (
    ContactQuery,
    HostQuery,
    Domain as DomainQuery
)
from domain_api.epp.entity import EppRpcClient
from domain_api.models import (
    Contact,
    RegisteredDomain,
    Nameserver,
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
        self.info_contact_response = {
            "contact:infData": {
                "contact:authInfo": {
                    "contact:pw": "iafbv5yoe5cg4k8cww44kk0400wg8gg"
                },
                "contact:clID": "H93060719",
                "contact:crDate": "2017-01-23T02:48:25.0Z",
                "contact:crID": "H93060719",
                "contact:disclose": {
                    "contact:email": {},
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

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    @patch.object(ContactQuery, 'process_disclose')
    def test_disclose_processing(self, process_disclose):
        """
        Test process disclose is called.
        """
        contact_query = ContactQuery(Contact.objects.all())
        with patch.object(EppRpcClient,
                          'call',
                          return_value=self.info_contact_response):
            contact = Contact.objects.get(registry_id='contact-123')
            contact_query.info(contact)
            process_disclose.assert_called_with( {
                "contact:email": {},
                "contact:name": {
                    "type": "int"
                },
                "contact:org": {
                    "type": "int"
                },
                "contact:voice": {},
                "flag": "1"
            })

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_info_domain(self):
        """
        Test info domain processing.
        """
        contact_query = ContactQuery(
            Contact.objects.filter(user=self.user)
        )
        with patch.object(EppRpcClient,
                          'call',
                          return_value=self.info_contact_response):
            contact = Contact.objects.get(registry_id='contact-123')
            contact = contact_query.info(contact)
            print("Contact: {!r}".format(contact))
            self.assertEqual("admin@test.com",
                             contact["email"],
                             "Response from info request contains email"
                             )
            self.assertEqual("reg-20",
                             contact["registry_id"],
                             "contact id is expected value")
            self.assertEqual(contact["country"], "US", "Expected country US")
            self.assertEqual(set(contact["non_disclose"]),
                             set([
                                 "address",
                                 "fax"
                             ]),
                             "Non disclose data is correct"
                             )



class TestNameserver(TestSetup):

    """
    Test processing Nameserver queries/management
    """

    def setUp(self):
        """
        Setup test suite

        """
        super().setUp()
        self.info_host_response = {
            "host:infData": {
                "xmlns:host": "urn:ietf:params:xml:ns:host-1.0",
                "host:name": "ns3.test-18-06-02.xyz",
                "host:roid": "H266917-CNIC",
                "host:status": {
                    "s": "ok"
                },
                "host:addr": {
                    "ip": "v4",
                    "$t": "22.33.44.55"
                },
                "host:clID": "H93060719",
                "host:crID": "H93060719",
                "host:crDate": "2017-06-23T07:16:52.0Z"
            }
        }

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

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    @patch.object(HostQuery, 'process_status')
    @patch.object(HostQuery, 'process_addresses')
    def test_info_host_helper_functions(self, proc_addresses, proc_status):
        """
        Test helper functions are called for info host.
        """
        registered_host = Nameserver.objects.get(idn_host='ns1.test-01.cx')
        host_query = HostQuery()
        with patch.object(EppRpcClient,
                          'call',
                          return_value=self.info_host_response):
            host_query.info(registered_host)
            proc_status.assert_called_with({ "s": "ok" })
            proc_addresses.assert_called_with({
                "ip": "v4",
                "$t": "22.33.44.55"
            })


class TestDomain(TestSetup):

    def setUp(self):
        super().setUp()
        self.info_domain_response = {
            "domain:infData": {
                "xmlns:domain": "urn:ietf:params:xml:ns:domain-1.0",
                "domain:name": "test-something.bar",
                "domain:roid": "D2357923-CNIC",
                "domain:status": {
                    "s": "ok"
                },
                "domain:registrant": "2df4a9dd",
                "domain:contact": [
                    { "type": "tech", "$t": "0b8747b2" },
                    { "type": "admin", "$t": "a1c00cc2" }
                ],
                "domain:ns": {
                    "domain:hostObj": [
                        "ns1.nameserver.com",
                        "ns2.nameserver.com"
                    ]
                },
                "domain:clID": "H93060719",
                "domain:crID": "H93060719",
                "domain:crDate": "2017-06-18T01:27:26.0Z",
                "domain:upDate": "2017-06-18T01:27:26.0Z",
                "domain:exDate": "2018-06-18T23:59:59.0Z",
                "domain:authInfo": {
                    "domain:pw": "2dxr6n0if8n"
                }
            }
        }

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    @patch.object(DomainQuery, 'process_status')
    @patch.object(DomainQuery, 'process_nameservers')
    def test_info_domain_calls_process_functions(self,
                                                 proc_nameservers,
                                                 proc_status):
        """
        Test that succesful info domain with nameserver data calls
        process_nameservers.
        """
        queryset= RegisteredDomain.objects.all()
        dq = DomainQuery(queryset)
        with patch.object(EppRpcClient,
                          'call',
                          return_value=self.info_domain_response):
            dq.info('test-something.bar')
            proc_nameservers.assert_called_with( {
                "domain:hostObj": [
                    "ns1.nameserver.com",
                    "ns2.nameserver.com"
                ]
            })
            proc_status.assert_called_with({"s": "ok"})

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_info_domain_nameserver_processing(self):
        """
        Test processing info domain response for nameserver handling.
        """
        queryset= RegisteredDomain.objects.all()
        domain_query = DomainQuery(queryset)
        with patch.object(EppRpcClient,
                          'call',
                          return_value=self.info_domain_response):
            return_data, registered_domain = domain_query.info('test-something.bar')
            self.assertIn("nameservers",
                          return_data,
                          "Return data contains nameservers")
            self.assertEqual(return_data["nameservers"],
                             ["ns1.nameserver.com", "ns2.nameserver.com"],
                             "Info domain processed nameservers correctly")
