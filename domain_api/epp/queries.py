import os
from ..utilities.rpc_client import EppRpcClient


class Domain(object):

    """
    Query operations for domains.
    """

    def __init__(self):
        """
        Initialise Domain object.
        """
        rabbit_host = os.environ.get('RABBIT_HOST')
        self.rpc_client = EppRpcClient(host=rabbit_host)

    def check_domain(self, registry, *args):
        """
        Send a check domain request to the registry.

        :*args: TODO
        :returns: TODO

        """
        data = {"domain": [args]}
        response_data = self.rpc_client.call(registry, 'checkDomain', data)
        available = response_data["domain:chkData"]["domain:cd"]["domain:name"]["avail"]
        is_available = False
        if available and int(available) == 1:
            is_available = True
        availability = {
            "result": [
                {
                    "domain": args[0],
                    "available": is_available
                }
            ]
        }
        return availability
