from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch
from domain_api.views import EppRpcClient
from ..exceptions import EppError


class TestCheckDomain(TestCase):

    def setUp(self):
        """
        Set up test suite
        :returns: TODO

        """
        self.client = Client()
        self.user = User.objects.create_user(
            username="testcustomer",
            email="testcustomer@test.com",
            password="secret"
        )


    def login_client(self):
        """
        Log user in to API.

        :returns: logged in session
        """
        self.client.login(username="testcustomer", password="secret")

    def test_epp_error(self):
        """
        An epp error should result in a 400 bad request
        """
        self.login_client()

        with patch.object(EppRpcClient, 'call', side_effect=EppError("FAIL")):
            response = self.client.get(
                '/domain-api/check-domain/test-registry/whatever.tld'
            )
            self.assertEqual(response.status_code,
                             400,
                             "EPP error caused a 400 bad request.")
