from ..models import TopLevelDomain
from ..exceptions import InvalidTld


def parse_domain(fqdn):
    """
    Parse a domain into name and tld components.

    Note: resolution of a domain will depend on the TLDs that are currently
    provided by our TopLevelDomain table.

    :fqdn: a fully qualified domain name
    :returns: dict containing name and tld

    """
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
