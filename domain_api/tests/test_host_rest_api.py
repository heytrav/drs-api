from unittest.mock import patch
import json
import domain_api
from ..workflows import CentralNic
from domain_api.epp.entity import EppRpcClient
from .test_setup import TestSetup


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestHostApi(TestSetup):

    """
    Test api interaction to manage host objects
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

    @patch('domain_api.epp.entity.EppRpcClient', new=MockRpcClient)
    @patch.object(CentralNic, 'create_host')
    def test_create_new_nameserver(self, mock_create_host):
        """
        Test a nameserver creation
        """
        create_host_data = {
            "idn_host": "ns1.test-something.bar",
            "addr": [
                "11.22.33.44",
                {
                    "ip": "::FF:0::E::",
                    "type": "v6"
                }
            ]
        }
        return_value = {
            "host": "ns1.test-something.bar"
        }
        with patch.object(EppRpcClient,
                          'call',
                          return_value=return_value):
            jwt_header = self.api_login()
            self.client.post('/v1/hosts/',
                             data=json.dumps(create_host_data),
                             content_type="application/json",
                             HTTP_AUTHORIZATION=jwt_header)
            mock_create_host.assert_called_with(create_host_data,
                                                self.test_customer_user)
