from .test_setup import TestSetup

class TestApiClient(TestSetup):

    def login_client(self):
        """
        Log user in to API.

        :returns: logged in session
        """
        self.client.login(username="testcustomer", password="secret")
