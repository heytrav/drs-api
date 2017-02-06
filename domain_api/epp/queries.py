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

    def info(self, registry, domain, is_staff=False):
        """
        Get info for a domain

        :registry: str registry to query
        :domain: str domain name to query
        :returns: dict with info about domain

        """
        data = {"domain": domain}
        response_data = self.rpc_client.call(registry, 'infoDomain', data)
        info_data = response_data["domain:infData"]
        for contact in info_data["domain:contact"]:
            if '$t' in contact:
                contact["handle"] = contact["$t"]
                contact["contact_type"] = contact["type"]
                del contact["type"]
                del contact["$t"]
        return_data = {
            "domain": info_data["domain:name"],
            "status": info_data["domain:status"],
            "registrant": info_data["domain:registrant"],
            "contacts": info_data["domain:contact"],
            "ns": info_data["domain:ns"]["domain:hostObj"],
        }
        if is_staff:
            return_data["auth_info"] = info_data["domain:authInfo"]["domain:pw"]
            return_data["roid"] = info_data["domain:roid"]
        log.info(return_data)
        return return_data

