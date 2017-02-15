from django_logging import log
from ..models import (
    ContactType,
    ContactHandle,
    RegistrantHandle,
    Domain,
    RegisteredDomain,
    TopLevelDomain,
    TopLevelDomainProvider,
)
from ..serializers import ContactHandleSerializer, RegistrantHandleSerializer
from ..exceptions import UnsupportedTld, InvalidTld, NoTldManager
from domain_api.epp.actions.contact import Contact


class DomainManager(object):

    """
    Base class for domain managers.
    """

    def __init__(self,
                 domain,
                 tld):
        """
        Manage basic operations for domain objects.
        """
        self.domain = domain
        self.tld = tld

    def get_registrant_handle(self, arg1):
        """TODO: Docstring for get_registrant_handle.

        :arg1: TODO
        :returns: TODO

        """
        pass

    def create_domain(self, data):
        """
        Register a domain
        :returns: TODO

        """
        domain = data["domain"]
        registrant = RegistrantHandle.objects.get(pk=data['registrant'])
        contacts = data.get('contacts', [])
        admin = ContactHandle.objects.get(pk=data['admin'])
        tech = ContactHandle.objects.get(pk=data['tech'])
        try:
            domain_obj = Domain.objects.get(name=self.domain)
        except Domain.DoesNotExist:
            domain_obj = Domain(
                name=self.domain,
                idn=idna.ToASCII(self.domain)
            )
            domain_obj.save()
        epp_request = {
            "name": domain,
            "registrant": registrant.handle,
            "contact": [
                {"admin": admin.handle},
                {"tech": tech.handle}
            ],
            "ns": [
                "ns1.hexonet.net",
                "ns2.hexonet.net"
            ]
        }
        log.info(epp_request)


class CentralNic(DomainManager):

    """
    Manage CentralNic domain operations.
    """

    def __init__(self, domain, tld):
        super().__init__(domain, tld)


class DomainManagerFactory(object):

    """
    Manage what registry will register a domain.
    """

    tld_managers = {
        "centralnic-test": CentralNic
    }

    def __init__(self):
        """
        Set up factory.
        """
        self.tlds = TopLevelDomain.objects.all()

    def get_manager(self, fqdn):
        """
        From TLD, determine which registry to use for a domain operation.

        :fqdn: fully qualified domain we are attempting to process
        :returns: a domain manager
        """
        log.debug({"message": "Find manager for domain", "domain": fqdn})
        probable_tld = None
        length = 0
        domain_name = None
        for tld in self.tlds:
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
        try:
            # See if this TLD is provided by one of our registries.
            tld_provider = TopLevelDomainProvider.objects.get(zone=probable_tld)
            slug = tld_provider.provider.slug
            return self.tld_managers[slug](domain_name,
                                           probable_tld)
        except TopLevelDomainProvider.DoesNotExist:
            raise UnsupportedTld(probable_tld)
        except KeyError:
            raise NoTldManager(slug)