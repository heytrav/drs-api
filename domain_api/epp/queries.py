from django.db.models import Q
from django_logging import log
from ..utilities.domain import parse_domain, get_domain_registry
from ..exceptions import UnknownContact, UnknownRegistry
from ..models import (
    Contact as ContactModel,
    Registrant as RegistrantModel,
    RegisteredDomain
)
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

        :check_data: item from a set of check domain results
        :returns: availability with epp attributes renamed

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


    def info(self, domain, registry, user=None):
        """
        Get info for a domain

        :registry: str registry to query
        :domain: str domain name to query
        :returns: dict with info about domain

        """

        parsed_domain = parse_domain(domain)
        user_registered_domain_set = RegisteredDomain.objects.filter(
            Q(registrant__registrant__project_id=user) | Q(contacts__contact__project_id=user)
        )
        registered_domain_set = user_registered_domain_set.filter(
            domain__name=parsed_domain["domain"],
            tld__zone=parsed_domain["zone"],
            active=True
        )
        is_owner = False
        if registered_domain_set.count() > 0:
            is_owner = True
        data = {"domain": domain}
        response_data = self.rpc_client.call(registry, 'infoDomain', data)
        info_data = response_data["domain:infData"]
        for contact in info_data["domain:contact"]:
            if '$t' in contact:
                contact_type = contact["type"]
                contact_id = contact["$t"]
                contact[contact_type] = contact_id
                del contact["type"]
                del contact["$t"]
        return_data = {
            "domain": info_data["domain:name"],
            "registrant": info_data["domain:registrant"],
            "contacts": info_data["domain:contact"],
            "ns": self.process_nameservers(info_data["domain:ns"]),
            "status": self.process_status(info_data["domain:status"])
        }

        if (is_owner or user.is_staff) and "domain:authInfo" in info_data:
            return_data["authcode"] = info_data["domain:authInfo"]["domain:pw"]
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
            "company": item.get("contact:org", ""),
            "postal_info_type": item["type"],
            "street1": " ".join(contact_street),
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
        flag = False
        if int(raw_disclose_data["flag"]) == 1:
            flag = True
        contact_attributes = {
            "contact:name": "disclose_name",
            "contact:voice": "disclose_telephone",
            "contact:fax": "disclose_fax",
            "contact:email": "disclose_email",
            "contact:addr": "disclose_address",
            "contact:org": "disclose_company"
        }
        disclose = {}
        for epp_attr, item in contact_attributes.items():
            if epp_attr in raw_disclose_data:
                disclose[item] = flag
        return disclose

    def info(self, registry_id, user=None, registry=None):
        """
        Fetch info for a contact

        :registry: Registry to query
        :contact: ID of contact
        :returns: dict of contact information

        """
        is_owner = False
        contact_queryset = ContactModel.objects.filter(project_id=user)
        registrant_queryset = RegistrantModel.objects.filter(project_id=user)
        if user.groups.filter(name='admin').exists():
            contact_queryset = ContactModel.objects.all()
            registrant_queryset = RegistrantModel.objects.all()
        # Find out if this contact is one of ours. If contact belongs to logged
        # in user or user is admin, return authcode data and other data.
        contact = None
        try:
            queryset = contact_queryset
            contact = queryset.get(registry_id=registry_id)
            is_owner = True
        except ContactModel.DoesNotExist:
            try:
                queryset = registrant_queryset
                contact = queryset.get(registry_id=registry_id)
                is_owner = True
            except RegistrantModel.DoesNotExist:
                log.warn({"contact": registry_id,
                          "message": "infoContact for unknown contact"})

        if registry is None:
            if contact:
                registry = contact.provider.slug
            else:
                raise UnknownRegistry("Cannot determine registry to query.")
        data = {"contact": registry_id}
        response_data = self.rpc_client.call(registry, 'infoContact', data)
        log.debug(response_data)
        info_data = response_data["contact:infData"]
        disclose_data = {}
        if "contact:disclose" in info_data:
            disclose_data = self.process_disclose(info_data["contact:disclose"])

        processed_postal_info = self.process_postal_info(
            info_data["contact:postalInfo"]
        )[0]
        processed_info_data = {
            "email": info_data["contact:email"],
            "fax": info_data.get("contact:fax", ""),
            "registry_id": info_data["contact:id"],
            "telephone": info_data["contact:voice"],
        }
        if (is_owner or user.is_staff):
            extra_fields = {}
            extra_fields["status"] = self.process_status(
                info_data["contact:status"]
            )
            extra_fields["roid"] = info_data["contact:roid"]
            if "contact:authInfo" in info_data:
                extra_fields["authcode"] = info_data["contact:authInfo"]["contact:pw"]
            processed_info_data = {**processed_info_data, **extra_fields}

        try:
            contact_info_data = {
                **processed_postal_info,
                **processed_info_data,
                **disclose_data
            }
            for item, value in contact_info_data.items():
                if isinstance(value, dict):
                    contact_info_data[item] = ""

            if contact and is_owner:
                queryset.filter(pk=contact.id).update(**contact_info_data)
            log.info(contact_info_data)
        except Exception as e:
            log.error({"error": e});
            raise e
        log.debug({"processed_info": processed_info_data})
        return contact_info_data
