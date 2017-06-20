from django.test import TestCase
import jsonschema
from .. import schemas
from jsonschema.exceptions import ValidationError


class TestValidation(TestCase):

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
            raise
        return True


class TestNameserverValidation(TestValidation):

    """
    Test validation of nameserver data structures.
    """

    def test_mixed_ip_addr_validation(self):
        """
        Test validation of mixed string ip and ip objects.

        """
        nameserver = {
            "host": "ns1.nameserver.com",
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
        result = self.validator(nameserver, schemas.nameserver)
        self.assertTrue(result, "Valid nameserver")

    def test_dict_field_ip_addr_validation(self):
        """
        Test validation of nameserver with host ip objects.

        """
        nameserver = {
            "host": "ns1.nameserver.com",
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
        result = self.validator(nameserver, schemas.nameserver)
        self.assertTrue(result, "Valid nameserver")

    def test_string_field_ip_addr_validation(self):
        """
        Test validation of nameserver with missing host.

        """
        nameserver = {
            "addr": [
                "11.22.33.44", "22.33.44"
            ]
        }
        with self.assertRaises(ValidationError):
            self.validator(nameserver, schemas.nameserver)

    def test_name_only_validation(self):
        """
        Test validation of nameserver missing addr field.
        """
        nameserver = {
            "host": "ns1.nameserver.com"
        }
        with self.assertRaises(ValidationError):
            self.validator(nameserver, schemas.nameserver)


class TestIpValidation(TestValidation):

    def test_ip_mixed_set(self):
        """
        Test validation of a mixed set of strings and objects.

        """
        ip_addr = [
            "11.22.33.44",
            {
                "ip": "::FF::0::",
                "type": "v6"
            },
            {
                "ip": "12.33.44.55"
            }
        ]
        result = self.validator(ip_addr, schemas.ip_addr)
        self.assertTrue(result, "Validates mixed set of ip addresses")

    def test_ip_objects_only(self):
        """
        Test validation of a set of objects.

        """
        ip_addr = [
            {
                "ip": "11.22.33.44",
                "type": "v4"
            },
            {
                "ip": "::FF::0::",
                "type": "v6"
            },
            {
                "ip": "12.33.44.55"
            }
        ]
        result = self.validator(ip_addr, schemas.ip_addr)
        self.assertTrue(result, "Validates mixed set of ip addresses")

    def test_fail_ip_validation(self):
        """
        Test validation of empty ip set

        """
        ip_addr = []
        with self.assertRaises(ValidationError):
            self.validator(ip_addr, schemas.ip_addr)
