from django.test import TestCase
import jsonschema
from .. import schemas


class TestNameserverValidation(TestCase):

    """
    Test validation of nameserver data structures.
    """

    def test_ip_addr_validation(self):
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
        jsonschema.validate(nameserver, schemas.ip_field)
        self.assertTrue(True)
