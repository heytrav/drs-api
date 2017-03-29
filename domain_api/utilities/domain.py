from ..exceptions import InvalidTld, UnsupportedTld
import idna
from ..models import (
    Domain,
    TopLevelDomain,
    TopLevelDomainProvider,
    RegisteredDomain,
    NameserverHost,
    IpAddress,
)


def get_domain_registry(fqdn):
    """
    Fetch the registry for a given domain.
    In the future there may be more than one upstream provider for a particular
    domain. If it is one registered in our system it should already be
    connected to one, but if not we should default to one particular registry.

    :fqdn: str domain
    :returns: DomainProvider object

    """
    parsed_domain = parse_domain(fqdn)
    tld_provider = None
    try:
        top_level_domain = TopLevelDomain.objects.get(
            zone=parsed_domain["zone"]
        )
        domain_obj, _ = Domain.objects.get_or_create(
            name=parsed_domain["domain"],
        )
        registered_domain_set = RegisteredDomain.objects.filter(
            domain=domain_obj,
            tld=top_level_domain,
            active=True
        )
        if registered_domain_set.count() > 0:
            registered_domain = registered_domain_set.first()
            tld_provider = registered_domain.tld_provider
        else:
            tld_provider = TopLevelDomainProvider.objects.get(
                zone=top_level_domain
            )
        return tld_provider.provider
    except TopLevelDomainProvider.DoesNotExist:
        raise UnsupportedTld(parsed_domain["zone"])
    except Exception as e:
        raise e


def parse_domain(fqdn):
    """
    Parse a domain into name and tld components.

    Note: resolution of a domain will depend on the TLDs that are currently
    provided by our TopLevelDomain table.

    :fqdn: a fully qualified domain name
    :returns: dict containing name and tld

    """
    fqdn = idna.encode(fqdn, uts46=True).decode('ascii')
    tlds = TopLevelDomain.objects.all()
    probable_tld = None
    length = 0
    domain_name = None
    for tld in tlds:
        zone = "." + tld.zone
        endindex = - (len(zone))
        if zone == fqdn[endindex:] and len(zone) > length:
            probable_tld = tld
            length = len(zone)
            # Get the actual domain name. Make sure it doesn't have
            # any subdomain prefixed
            domain_name = fqdn[:endindex].split(".")[-1]
    if domain_name is None or len(domain_name) == 0:
        raise InvalidTld(fqdn)
    return {"domain": domain_name, "zone": probable_tld.zone}


def synchronise_domain(info_data, domain_id):
    """
    Synchronise data in info domain response with upstream registry.

    :info_data: dict containing info data from registry
    :registered_domain: int primary key of domain
    """
    RegisteredDomain.objects.filter(pk=domain_id).update(
        authcode=info_data["authcode"],
        roid=info_data["roid"],
        status=info_data["status"]
    )

def synchronise_host(info_data, host_id):
    """
    Synchronise data in info host response from upstream registry.

    :info_data: dict containing info data from the registry
    :host_id: int primary key of host

    """
    nshost = NameserverHost.objects.filter(pk=host_id)
    nshost.update(
        status=info_data["status"],
        roid=info_data["roid"]
    )
    nshost_obj = nshost.get(pk=host_id)
    for addr in info_data["addr"]:
        address_type = addr["addr_type"]
        ip = addr["ip"]
        if not IpAddress.objects.filter(ip=ip).exists():
            IpAddress.objects.get_or_create(
                ip=ip,
                nameserver_host=nshost_obj,
                address_type=address_type,
                project_id=nshost_obj.project_id
            )
