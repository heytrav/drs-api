from django.test import TestCase

from domain_api.serializers import (
    InfoHostSerializer
)


class TestSerialization(TestCase):

    """
    Test correctness of basic serialization methods
    """

    def test_info_host_only_ipv4(self):
        """
        Test handling of info host data
        """
        sample_data  = {
            "host": "ns.somehost.tld",
            "addr": [
                {"ip": "22.45.67.89"},
                {"addr_type": "v4", "ip": "23.45.68.89"},
                {"addr_type": "v4", "ip": "24.45.69.89"}
            ]
        }
        serializer = InfoHostSerializer(data=sample_data)
        valid = serializer.is_valid()
        self.assertTrue(valid)

    def test_info_host_no_ip_fail(self):
        """
        Test serializer should fail when no IPs present
        """
        sample_data  = {
            "host": "ns.somehost.tld",
            "addr": [ ]
        }
        serializer = InfoHostSerializer(data=sample_data)
        valid = serializer.is_valid()
        self.assertFalse(valid)
