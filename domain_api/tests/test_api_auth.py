from .test_api_interaction import TestApiClient


class TestAPIAuth(TestApiClient):

    def setUp(self):
        super().setUp()

    def api_login(self):
        """
        Log client in using api-token-auth endpoint
        :returns: TODO

        """
        credentials = {
            "username": "testcustomer",
            "password": "secret"
        }
        response = self.client.post('/api-token-auth',
                                    secure=True,
                                    data=credentials)
        data = response.data
        return data["token"]

    def test_unauth_endpoint_denied(self):
        """
        Test accessing an endpoint without JWT is denied.

        """
        response = self.client.get('/v1/account-detail/1/')
        self.assertEqual(response.status_code,
                         403,
                         "Not allowed to access endoint without JWT")

    def test_authorized_endpoint_accepted(self):
        """
        Test accessing an endpoint with JWT is allowed.

        """
        token = self.api_login()
        jwt_header = 'JWT ' + token
        response = self.client.get('/v1/account-detail/1/',
                                   HTTP_AUTHORIZATION=jwt_header)
        self.assertEqual(response.status_code,
                         200,
                         "Allwed to request endpoint with JWT.")
