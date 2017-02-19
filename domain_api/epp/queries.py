from django_logging import log
from .entity import EppEntity


class Domain(EppEntity):

    """
    Query operations for domains.
    """

    def __init__(self):
        """
        Initialise Domain object.
        """
        super().__init__()

    def process_availability_item(self, check_data):
        """
        Process check domain items.

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
        data = {"domain": [args]}
        log.debug(data)
        response_data = self.rpc_client.call(registry, 'checkDomain', data)
        log.debug({"response data": response_data})
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
        nameservers = []
        ns = info_data["domain:ns"]
        for host in ns["domain:hostObj"]:
            nameservers.append(host)
        return_data = {
            "domain": info_data["domain:name"],
            "status": {"status": info_data["domain:status"]},
            "registrant": info_data["domain:registrant"],
            "contacts": info_data["domain:contact"],
            "ns": nameservers,
        }
        if is_staff:
            return_data["auth_info"] = info_data["domain:authInfo"]["domain:pw"]
            return_data["roid"] = info_data["domain:roid"]
        log.info(return_data)
        return return_data


class Contact(EppEntity):

    """
    Contact EPP operations.
    """

    def __init__(self):
        super().__init__()

    def process_postal_info(self, postal_info):
        """
        Process postal info part of info contact response
        :returns: list of postal info objects

        """
        processed_postal = []
        if isinstance(postal_info, list):
            processed_postal += [self.postal_info_item(i) for i in postal_info]
        else:
            processed_postal.append(self.postal_info_item(postal_info))
        return processed_postal

    def postal_info_item(self, item):
        """
        Process individual postal info item

        :item: dict containing raw EPP postalInfo data
        :returns: dict containing info with namespaces removed

        """
        addr = item["contact:addr"]
        contact_street = []
        raw_street = addr["contact:street"]
        if isinstance(raw_street, list):
            contact_street += raw_street
        else:
            contact_street.append(raw_street)
        return {
            "name": item["contact:name"],
            "org": item.get("contact:org", ""),
            "type": item["type"],
            "addr": {
                "street": contact_street,
                "cc": addr["contact:cc"],
                "sp": addr["contact:sp"],
                "city": addr["contact:city"],
                "pc": addr["contact:pc"]
            }
        }

    def info(self, registry, contact):
        """
        Fetch info for a contact

        :registry: Registry to query
        :contact: ID of contact
        :returns: dict of contact information

        """
        data = {"contact": contact}
        response_data = self.rpc_client.call(registry, 'infoContact', data)
        log.debug(response_data)
        info_data = response_data["contact:infData"]

        processed_info_data = {
            "email": info_data["contact:email"],
            "fax": info_data.get("contact:fax", ""),
            "id": info_data["contact:id"],
            "postal_info": self.process_postal_info(
                info_data["contact:postalInfo"]
            )
        }
        log.debug({"processed_info": processed_info_data})
        return processed_info_data
