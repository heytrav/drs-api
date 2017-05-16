from unittest.mock import patch
import json
import domain_api
from domain_api.epp.entity import EppRpcClient
from ..exceptions import EppError
from .test_setup import TestSetup


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestCheckDomain(TestSetup):

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
                '/v1/domains/whatever.ote/'
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
                        "$t": "whatever.ote"
                    }
                }
            }
        }
        with patch.object(EppRpcClient, 'call', return_value=return_data):
            response = self.client.get(
                '/v1/available/whatever.ote/'
            )
            self.assertEqual(response.status_code,
                             200,
                             "Epp returned normally")
            data = response.data
            self.assertTrue(data["available"],
                            "Serialised a check_domain response")


class TestInfoDomain(TestSetup):

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
                "domain:name": "whatever.ote",
                "domain:status": "ok",
                "domain:registrant": "R1234",
                "domain:ns": [
                    {"domain:hostObj": "ns1.nameserver.com"},
                    {"domain:hostObj": "ns2.nameserver.com"}
                ],
                "domain:contact": [
                    {"$t": "A1234", "type": "admin"},
                    {"$t": "T1234", "type": "tech"}
                ]
            }
        }
        with patch.object(EppRpcClient, 'call', return_value=return_value):
            response = self.client.get(
                '/v1/domains/whatever.ote/'
            )
            self.assertEqual(response.status_code,
                             200,
                             "Epp returned normally")


class TestContact(TestSetup):

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
                    "contact:name": [{"type": "loc"}, {"type": "int"}],
                    "contact:org": [{"type": "loc"}, {"type": "int"}],
                    "contact:addr": [{"type": "loc"}, {"type": "int"}],
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
                    "contact:name": [{"type": "loc"}, {"type": "int"}],
                    "contact:org": [{"type": "loc"}, {"type": "int"}],
                    "contact:addr": [{"type": "loc"}, {"type": "int"}],
                    "contact:voice": {},
                    "contact:fax": {},
                    "contact:email": {}
                }
            }
        }
        with patch.object(EppRpcClient,
                          'call',
                          return_value=info_contact_response):
            response = self.client.get('/v1/contacts/contact-321/')
            self.assertEqual(response.status_code,
                             200,
                             "Info contact returned normal response")



class TestRegistrant(TestSetup):


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


class TestBasicQueries(TestSetup):

    def test_unauthenticated_endpoint_denied(self):
        """
        Test accessing an endpoint without JWT is denied.

        """
        response = self.client.get('/v1/account-details/1/')
        self.assertEqual(response.status_code,
                         403,
                         "Not allowed to access endoint without JWT")

    def test_authenticateded_endpoint_accepted(self):
        """
        Test accessing an endpoint with JWT is allowed.

        """
        jwt_header = self.api_login()
        joes_id = self.joe_user.pk
        path = "/v1/account-details/%s/" % joes_id
        response = self.client.get(path,
                                   HTTP_AUTHORIZATION=jwt_header)
        self.assertEqual(response.status_code,
                         200,
                         "Allowed to request endpoint with JWT.")

    def test_unauthorized_endpoint_denied(self):
        """
        Test access to admin level object denied.
        """
        jwt_header = self.api_login()
        response = self.client.get('/v1/tld-providers/',
                                   HTTP_AUTHORIZATION=jwt_header)
        self.assertEqual(response.status_code,
                         403,
                         "Normal logged in user cannot  access tld-provider")

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    def test_check_domain_response(self):
        """
        Check domain using JWT to authenticate

        """
        jwt_header = self.api_login()
        return_data = {
            "domain:chkData": {
                "domain:cd": {
                    "domain:name": {
                        "avail": 1,
                        "$t": "whatever.ote"
                    }
                }
            }
        }
        with patch.object(EppRpcClient, 'call', return_value=return_data):
            response = self.client.get(
                '/v1/available/whatever.ote/',
                HTTP_AUTHORIZATION=jwt_header
            )
            self.assertEqual(response.status_code,
                             200,
                             "Epp returned normally")
            data = response.data
            self.assertTrue(data["available"],
                            "Serialised a check_domain response")


class TestHostApi(TestSetup):

    """
    Test api interaction to manage host objects
    """

    def setUp(self):
        """
        Setup test suite

        """
        super().setUp()

    def test_create_incorrect_data(self):
        """
        Should get an error when incorrectly structured host request sent to
        api.

        """
        bad_create_host = {
            "host": "ns1.somehost.com",
            "addr": [
                {"ip_addr": "23.34.45.67"},
            ]
        }
        jwt_header = self.api_login()
        response = self.client.post('/v1/hosts/',
                                    data=json.dumps(bad_create_host),
                                    content_type="application/json",
                                    HTTP_AUTHORIZATION=jwt_header)
        self.assertEqual(response.status_code,
                         400,
                         "incorrect create host datastructure returns 400")
        self.assertEqual('This field is required.',
                         response.data['addr']['ip'][0],
                         "ip field is required")
