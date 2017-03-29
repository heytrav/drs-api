from .test_api_auth import TestAPIAuth
import json


class TestHostApi(TestAPIAuth):

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
