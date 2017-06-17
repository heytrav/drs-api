import logging
from ..utilities.domain import parse_domain, get_domain_registry
import idna
from .entity import EppEntity

log = logging.getLogger(__name__)


class Domain(EppEntity):

    """
    Query operations for domains.
    """

    def __init__(self, queryset=None):
        """
        Initialise Domain object.
        """
        super().__init__(queryset)

    def process_contact_set(self, contacts):
        """
        Process a set of 1 or more contacts

        :contacts: dict or list of contacts
        :returns: list of dict objects

        """
        if isinstance(contacts, list):
            return [self.process_contact_item(i) for i in contacts]
        return [self.process_contact_item(contacts)]

    def process_contact_item(self, contact):
        """
        Process a single contact item.

        :contact: dict object containing contact data
        :returns: dict with contact-type mapping to id

        """
        if '$t' in contact:
            processed = {}
            contact_type = contact["type"]
            contact_id = contact["$t"]
            processed[contact_type] = contact_id
            return processed
        return None

    def check_domain(self, *args):
        """
        Send a check domain request to the registry.

        :*args: one or more domain names
        :returns: dict with set of results indicating availability

        """
        registry = get_domain_registry(args[0])
        data = {"domain": [idna.encode(i, uts46=True).decode('ascii')
                           for i in args]}
        log.debug("{!r}".format(data))
        response_data = self.rpc_client.call(registry.slug, 'checkDomain', data)
        log.debug("response data {!r}".format(response_data))
        check_data = response_data["domain:chkData"]["domain:cd"]
        results = []
        if isinstance(check_data, list):
            for item in check_data:
                results.append(self.process_availability_item(item, "domain"))
        else:
            results.append(self.process_availability_item(check_data, "domain"))

        availability = {
            "result": results
        }
        return availability

    def process_nameservers(self, raw_ns):
        """
        Process nameserver information in info domain

        :raw_ns: dict with raw nameserver info from EPP
        :returns: list of nameservers

        """
        nameservers = []
        if isinstance(raw_ns, dict) and "domain:hostObj" in raw_ns:
            ns_host = raw_ns["domain:hostObj"]
            if isinstance(ns_host, list):
                for host in ns_host:
                    nameservers.append(host)
            elif isinstance(ns_host, str):
                nameservers.append(ns_host)
        elif isinstance(raw_ns, list):
            for host_obj in raw_ns:
                nameservers.append(host_obj["domain:hostObj"])
        return nameservers

    def info(self, domain, user=None):
        """
        Get info for a domain

        :registry: str registry to query
        :domain: str domain name to query
        :returns: dict with info about domain

        """
        registry = get_domain_registry(domain)
        parsed_domain = parse_domain(domain)
        registered_domain_set = self.queryset.filter(
            name=parsed_domain["domain"],
            tld__zone=parsed_domain["zone"],
            active=True
        )
        registered_domain = None
        if registered_domain_set.exists():
            registered_domain = registered_domain_set.first()
        data = {"domain": domain}
        response_data = self.rpc_client.call(registry.slug, 'infoDomain', data)
        info_data = response_data["domain:infData"]
        return_data = {
            "domain": info_data["domain:name"],
            "registrant": info_data["domain:registrant"],
            "contacts": self.process_contact_set(info_data["domain:contact"]),
            "status": self.process_status(info_data["domain:status"])
        }
        if "domain:ns" in info_data:
            return_data["nameservers"] = self.process_nameservers(info_data["domain:ns"])

        if "domain:authInfo" in info_data:
            return_data["authcode"] = info_data["domain:authInfo"]["domain:pw"]
            return_data["roid"] = info_data["domain:roid"]
        log.info("Returning registered domain info")
        return (return_data, registered_domain)


class ContactQuery(EppEntity):

    """
    Contact EPP operations.
    """

    def __init__(self, queryset=None):
        super().__init__(queryset)

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
        if "contact:street" in addr:
            raw_street = addr["contact:street"]
            if isinstance(raw_street, list):
                contact_street += raw_street
            else:
                contact_street.append(raw_street)
        return {
            "name": item["contact:name"],
            "company": item.get("contact:org", ""),
            "postal_info_type": item["type"],
            "street": contact_street[0:3],
            "country": addr["contact:cc"],
            "state": addr["contact:sp"],
            "city": addr["contact:city"],
            "postcode": addr["contact:pc"]
        }

    def process_disclose(self, raw_disclose_data):
        """
        Extract information about disclosed attributes

        :raw_disclose_data: dict with disclose information from EPP
        :returns: dict processed with true/false

        """
        log.info("Processing disclose data {!r}".format(raw_disclose_data))
        contact_attributes = {
            "contact:voice": "telephone",
            "contact:fax": "fax",
            "contact:email": "email",
            "contact:name": "name",
            "contact:addr": "address",
            "contact:org": "company"
        }
        processed_data = {
            "flag": raw_disclose_data["flag"],
            "fields": []
        }
        for (k, v) in contact_attributes.items():
            processed_data["fields"].append(v)
        return processed_data

    def info(self, contact):
        """
        Fetch info for a contact

        :registry: Registry to query
        :contact: ID of contact
        :returns: dict of contact information

        """

        # Fetch contact from registry.
        data = {"contact": contact.registry_id}
        registry = contact.provider.slug
        response_data = self.rpc_client.call(registry, 'infoContact', data)
        log.debug("Received info response")
        info_data = response_data["contact:infData"]
        processed_postal_info = self.process_postal_info(
            info_data["contact:postalInfo"]
        )[0]
        processed_info_data = {
            "email": info_data["contact:email"],
            "fax": info_data.get("contact:fax", ""),
            "registry_id": info_data["contact:id"],
            "telephone": info_data["contact:voice"],

        }
        extra_fields = {}
        extra_fields["status"] = self.process_status(
            info_data["contact:status"]
        )
        extra_fields["roid"] = info_data["contact:roid"]
        if "contact:authInfo" in info_data:
            extra_fields["authcode"] = info_data["contact:authInfo"]["contact:pw"]
        processed_info_data.update(extra_fields)

        try:
            contact_info_data = {}
            contact_info_data.update(processed_postal_info)
            contact_info_data.update(processed_info_data)
            for item, value in contact_info_data.items():
                if isinstance(value, dict):
                    contact_info_data[item] = ""
            contact_info_data["disclose"] = self.process_disclose(
                info_data["contact:disclose"]
            )
            self.queryset.filter(pk=contact.id).update(**contact_info_data)
        except Exception as e:
            log.error("", exc_info=True)
            raise e
        return self.queryset.get(pk=contact.id)


class HostQuery(EppEntity):

    """
    Nameserver EPP operations
    """

    def __init__(self, queryset=None):
        super().__init__(queryset)

    def check_host(self, *args):
        """
        Send a check host request to the registry

        :*args: list of host names to check
        :returns: dict EPP check host response

        """
        registry = get_domain_registry(args[0])
        data = {"host": [idna.encode(i, uts46=True).decode('ascii')
                         for i in args]}
        response_data = self.rpc_client.call(
            registry.slug,
            'checkHost',
            data
        )
        check_data = response_data["host:chkData"]["host:cd"]
        results = []
        if isinstance(check_data, list):
            for item in check_data:
                results.append(self.process_availability_item(item, "host"))
        else:
            results.append(self.process_availability_item(check_data, "host"))

        availability = {
            "result": results
        }
        return availability

    def process_addr_item(self, item):
        """
        Process a host info address item

        :item: dict IP addr item
        :returns: dict with stuff parsed out

        """
        processed = {}
        if "$t" in item:
            processed["addr_type"] = item["ip"]
            processed["ip"] = item["$t"]
        return processed

    def process_addresses(self, addresses):
        """
        Process of a set host addresses

        :addresses: TODO
        :returns: TODO

        """
        if isinstance(addresses, list):
            return [self.process_addr_item(i) for i in addresses]
        return [self.process_addr_item(addresses)]

    def info(self, host, user=None):
        """
        Get info for a host

        :host: str host name to query
        :returns: dict with info about host

        """
        registry = get_domain_registry(host)
        registered_hosts = self.queryset.filter(
            nameserver__idn_host=idna.encode(host, uts46=True).decode('ascii'),
        )
        registered_host = None
        if registered_hosts.exists():
            registered_host = registered_hosts.first()

        data = {"name": host}
        response_data = self.rpc_client.call(registry.slug, 'infoHost', data)
        info_data = response_data["host:infData"]
        return_data = {
            "host": info_data["host:name"],
            "addr": self.process_addresses(info_data["host:addr"]),
            "nameserver_status": self.process_status(info_data["host:status"]),
            "roid": info_data["host:roid"]
        }
        if "host:authInfo" in info_data:
            return_data["authcode"] = info_data["host:authInfo"]["host:pw"]
            return_data["roid"] = info_data["host:roid"]
        return (return_data, registered_host)
