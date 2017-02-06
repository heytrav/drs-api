import os
from django_logging import log
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


    def process_availability_item(self, check_data):
        """TODO: Docstring for process_availability_.

        :check_data: TODO
        :returns: TODO

        """

        domain = check_data["domain:name"]['$t']
        response = {"domain": domain, "available": False}
        available = check_data["domain:name"]["avail"]
        if available and int(available) == 1:
            response["available"] = True
        else:
            response["available"] = False
            response["reason"] = check_data["domain:reason"]
        return response


    def check_domain(self, registry, *args):
        """
        Send a check domain request to the registry.

        :*args: one or more domain names
        :returns: dict with set of results indicating availability

        """
        data = {"domain": [*args]}
        log.debug(data)
        response_data = self.rpc_client.call(registry, 'checkDomain', data)
        check_data = response_data["domain:chkData"]["domain:cd"]
        results = []
        if isinstance(check_data, list):
            for item in check_data:
                results.append(self.process_availability_item(item))
        else:
            results.append(self.process_availability_item(check_data))

        availability = {
            "result": results
        }
        return availability
