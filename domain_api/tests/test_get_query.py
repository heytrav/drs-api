from unittest.mock import patch
import domain_api
import json
from ..models import (
    Contact,
    DomainContact,
    Registrant,
    DomainRegistrant
)
from domain_api.epp.entity import EppRpcClient
from ..exceptions import EppError
from .test_api_interaction import TestApiClient


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestCheckDomain(TestApiClient):

    def setUp(self):
        """
        Set up test suite

        """
        super().setUp()

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_epp_error(self):
        """
        An epp error should result in a 400 bad request.
        """
        self.login_client()

        with patch.object(EppRpcClient, 'call', side_effect=EppError("FAIL")):
            response = self.client.get(
                '/v1/domains/available/whatever.tld/'
            )
            self.assertEqual(response.status_code,
                             400,
                             "EPP error caused a 400 bad request.")

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_check_domain_response(self):
        """
        EPP check domain result returns serialized json response.
        """
        self.login_client()
        return_data = {
            "domain:chkData": {
                "domain:cd": {
                    "domain:name": {
                        "avail": 1,
                        "$t": "whatever.tld"
                    }
                }
            }
        }
        with patch.object(EppRpcClient, 'call', return_value=return_data):
            response = self.client.get(
                '/v1/domains/available/whatever.tld/'
            )
            self.assertEqual(response.status_code,
                             200,
                             "Epp returned normally")
            data = json.loads(response.content.decode('utf-8'))
            self.assertTrue(data["available"],
                            "Serialised a check_domain response")


class TestInfoDomain(TestApiClient):

    """
    Test info domain functionality
    """
    def setUp(self):
        """
        Set up test suite
        """
        super().setUp()

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_info_domain_response(self):
        """
        Test processing of info domain response
        """
        self.login_client()
        return_value = {
            "domain:infData": {
                "domain:name": "whatever.tld",
                "domain:status": "ok",
                "domain:registrant": "R1234",
                "domain:ns": [
                    { "domain:hostObj": "ns1.nameserver.com" },
                    { "domain:hostObj": "ns2.nameserver.com" }
                ],
                "domain:contact": [
                    { "$t": "A1234", "type": "admin", },
                    { "$t": "T1234", "type": "tech", }
                ]
            }
        }
        with patch.object(EppRpcClient, 'call', return_value=return_value):
            response = self.client.get(
                '/v1/domains/info/whatever.tld/'
            )
            self.assertEqual(response.status_code,
                             200,
                             "Epp returned normally")


class TestContact(TestApiClient):


    def setUp(self):
        """
        Set up test suite
        """
        super().setUp()
        self.contact = Contact(
            registry_id='contact-123',
            project_id=self.user,
            provider=self.provider,
            account_template=self.joe_user
        )
        self.contact.save()
        self.contact2 = Contact(
            registry_id='contact-124',
            project_id=self.user2,
            provider=self.provider,
            account_template=self.other_user
        )
        self.contact2.save()


    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_info_contact(self):
        """
        Test basic info contact
        """
        self.login_client()
        info_contact_response = {
            "contact:infData": {
                "xmlns:contact": "urn:ietf:params:xml:ns:contact-1.0",
                "xsi:schemaLocation": "urn:ietf:params:xml:ns:contact-1.0 contact-1.0.xsd",
                "contact:id": "contact-123",
                "contact:roid": "78442-CoCCA",
                "contact:status": [
                    {
                        "s": "linked",
                        "$t": "In use by 10 domains"
                    },
                    {
                        "s": "serverDeleteProhibited",
                        "$t": "Server locked: This contact is a domain registrant"
                    },
                    {
                        "s": "serverTransferProhibited",
                        "$t": "Server locked: This contact is a domain registrant"
                    },
                    {
                        "s": "serverUpdateProhibited",
                        "$t": "Server locked: This contact is a domain registrant"
                    }
                ],
                "contact:postalInfo": {
                    "type": "loc",
                    "contact:name": "Tester MacTesterson",
                    "contact:addr": {
                        "contact:street": "Haribo",
                        "contact:city": "Munich",
                        "contact:sp": "Bayern",
                        "contact:pc": "48392",
                        "contact:cc": "DE"
                    }
                },
                "contact:voice": "+49.89444134",
                "contact:email": "testy@testerson.com",
                "contact:clID": "catalyst_ote",
                "contact:crID": "catalyst_ote",
                "contact:crDate": "2017-03-03T10:06:33.063Z",
                "contact:upDate": "2017-03-05T21:22:07.154Z",
                "contact:upID": "catalyst_ote",
                "contact:disclose": {
                    "flag": "0",
                    "contact:name": [ { "type": "loc" }, { "type": "int" } ],
                    "contact:org": [ { "type": "loc" }, { "type": "int" } ],
                    "contact:addr": [ { "type": "loc" }, { "type": "int" } ],
                    "contact:voice": {},
                    "contact:fax": {},
                    "contact:email": {}
                }
            }
        }
        with patch.object(EppRpcClient,
                          'call',
                          return_value=info_contact_response):
            response = self.client.get('/v1/contacts/contact-123/')
            self.assertEqual(response.status_code,
                             200,
                             "Info contact returned normal response")


    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_info_contact_non_owner(self):
        """
        Test basic info contact for different user.
        """
        self.login_client()
        info_contact_response = {
            "contact:infData": {
                "xmlns:contact": "urn:ietf:params:xml:ns:contact-1.0",
                "xsi:schemaLocation": "urn:ietf:params:xml:ns:contact-1.0 contact-1.0.xsd",
                "contact:id": "contact-124",
                "contact:roid": "78442-CoCCA",
                "contact:status": [
                    {
                        "s": "linked",
                        "$t": "In use by 10 domains"
                    },
                    {
                        "s": "serverDeleteProhibited",
                        "$t": "Server locked: This contact is a domain registrant"
                    },
                    {
                        "s": "serverTransferProhibited",
                        "$t": "Server locked: This contact is a domain registrant"
                    },
                    {
                        "s": "serverUpdateProhibited",
                        "$t": "Server locked: This contact is a domain registrant"
                    }
                ],
                "contact:postalInfo": {
                    "type": "loc",
                    "contact:name": "Tester MacTesterson",
                    "contact:addr": {
                        "contact:street": "Haribo",
                        "contact:city": "Munich",
                        "contact:sp": "Bayern",
                        "contact:pc": "48392",
                        "contact:cc": "DE"
                    }
                },
                "contact:voice": "+49.89444134",
                "contact:email": "testy@testerson.com",
                "contact:clID": "catalyst_ote",
                "contact:crID": "catalyst_ote",
                "contact:crDate": "2017-03-03T10:06:33.063Z",
                "contact:upDate": "2017-03-05T21:22:07.154Z",
                "contact:upID": "catalyst_ote",
                "contact:disclose": {
                    "flag": "0",
                    "contact:name": [ { "type": "loc" }, { "type": "int" } ],
                    "contact:org": [ { "type": "loc" }, { "type": "int" } ],
                    "contact:addr": [ { "type": "loc" }, { "type": "int" } ],
                    "contact:voice": {},
                    "contact:fax": {},
                    "contact:email": {}
                }
            }
        }
        with patch.object(EppRpcClient,
                          'call',
                          return_value=info_contact_response):
            response = self.client.get('/v1/contacts/contact-124/')
            self.assertEqual(response.status_code,
                             200,
                             "Info contact returned normal response")



class TestRegistrant(TestApiClient):


    def setUp(self):
        """
        Set up test suite
        """
        super().setUp()
        self.contact = Registrant(
            registry_id='registrant-123',
            project_id=self.user,
            provider=self.provider,
            account_template=self.joe_user
        )
        self.contact.save()


    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_info_registrant(self):
        """
        Test basic info registrant
        """
        self.login_client()
        info_contact_response = {
            "contact:infData": {
                "xmlns:contact": "urn:ietf:params:xml:ns:contact-1.0",
                "xsi:schemaLocation": "urn:ietf:params:xml:ns:contact-1.0 contact-1.0.xsd",
                "contact:id": "registrant-123",
                "contact:roid": "78442-CoCCA",
                "contact:status": [
                    {
                        "s": "linked",
                        "$t": "In use by 10 domains"
                    },
                    {
                        "s": "serverDeleteProhibited",
                        "$t": "Server locked: This contact is a domain registrant"
                    },
                    {
                        "s": "serverTransferProhibited",
                        "$t": "Server locked: This contact is a domain registrant"
                    },
                    {
                        "s": "serverUpdateProhibited",
                        "$t": "Server locked: This contact is a domain registrant"
                    }
                ],
                "contact:postalInfo": {
                    "type": "loc",
                    "contact:name": "Tester MacTesterson",
                    "contact:addr": {
                        "contact:street": "Haribo",
                        "contact:city": "Munich",
                        "contact:sp": "Bayern",
                        "contact:pc": "48392",
                        "contact:cc": "DE"
                    }
                },
                "contact:voice": "+49.89444134",
                "contact:email": "testy@testerson.com",
                "contact:clID": "catalyst_ote",
                "contact:crID": "catalyst_ote",
                "contact:crDate": "2017-03-03T10:06:33.063Z",
                "contact:upDate": "2017-03-05T21:22:07.154Z",
                "contact:upID": "catalyst_ote",
                "contact:disclose": {
                    "flag": "0",
                    "contact:name": [ { "type": "loc" }, { "type": "int" } ],
                    "contact:org": [ { "type": "loc" }, { "type": "int" } ],
                    "contact:addr": [ { "type": "loc" }, { "type": "int" } ],
                    "contact:voice": {},
                    "contact:fax": {},
                    "contact:email": {}
                }
            }
        }
        with patch.object(EppRpcClient,
                          'call',
                          return_value=info_contact_response):
            response = self.client.get('/v1/registrants/registrant-123/')
            self.assertEqual(response.status_code,
                             200,
                             "Info contact returned normal response")
