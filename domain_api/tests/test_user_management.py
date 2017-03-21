from django.test import TestCase
from django.contrib.auth.models import User


class TestUserManagement(TestCase):

    """
    Test user creation.
    """

    def setUp(self):
        """
        Set up test suite.

        """
        super().setUp()

    def test_create_user(self):
        """
        Test successful user creation.
        """
        user_data = {
            "username": "mrrobot",
            "password": "secretpassword",
            "first_name": "Bob",
            "last_name": "Bot"
        }
        response = self.client.post('/register/',
                                    data=user_data)
        self.assertEqual(response.status_code,
                         201,
                         "Created a user")
        user = User.objects.get(username="mrrobot")
        self.assertEqual(user.first_name,
                         "Bob",
                         "Posting to /register endpoint created user")
