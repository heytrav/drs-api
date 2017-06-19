from django.test import TestCase
import jsonschema
from .. import schemas
from rest_framework.exceptions import ValidationError


class TestNameserverValidation(TestCase):

    """
    Test validation of nameserver data structures.
    """

    def validator(self, data, schema_field):
        """
        Perform validation and return a boolean indicating valid or not valid.

        :data: Data to validate
        :schema_field: schema to validate against
        :returns: Boolean

        """
        try:
            jsonschema.validate(data, schema_field)
        except ValidationError:
            return False
        return True

    def test_mixed_ip_addr_validation(self):
        """
        Test validatio of complete nameserver field
        :returns: TODO

        """
        nameserver = {
            "name": "ns1.nameserver.com",
            "addr": [
                "11.22.33.44",
                {
                    "ip": "22.33.44.55",
                    "type": "v4"
                },
                {
                    "ip": "22.33.44.55",
                },
                {
                    "ip": "::FE::0",
                    "type": "v6"
                },
            ]
        }
        result = self.validator(nameserver, schemas.ip_field)
        self.assertTrue(result, "Valid nameserver")

    def test_dict_field_ip_addr_validation(self):
        """
        Test validatio of complete nameserver field
        :returns: TODO

        """
        nameserver = {
            "name": "ns1.nameserver.com",
            "addr": [
                {
                    "ip": "22.33.44.55",
                    "type": "v4"
                },
                {
                    "ip": "22.33.44.55",
                },
                {
                    "ip": "::FE::0",
                    "type": "v6"
                },
            ]
        }
        result = self.validator(nameserver, schemas.ip_field)
        self.assertTrue(result, "Valid nameserver")

    def test_string_field_ip_addr_validation(self):
        """
        Test validatio of complete nameserver field
        :returns: TODO

        """
        nameserver = {
            "name": "ns1.nameserver.com",
            "addr": [
                "11.22.33.44", "22.33.44"
            ]
        }
        result = self.validator(nameserver, schemas.ip_field)
        self.assertTrue(result, "Valid nameserver")

    def test_name_only_validation(self):
        """
        Test validatio of complete nameserver field
        :returns: TODO

        """
        nameserver = {
            "name": "ns1.nameserver.com"
        }
        result = self.validator(nameserver, schemas.ip_field)
        self.assertTrue(result, "Valid nameserver")
