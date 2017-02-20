from django.test import TestCase, Client
from django.contrib.auth.models import User


class TestApiClient(TestCase):

    def setUp(self):
        """
        Set up test suite
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
