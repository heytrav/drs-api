from __future__ import absolute_import, unicode_literals
from celery import chain
from ..tasks import (
    check_domain,
    create_registry_contact
)
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


    def create_domain(self, data):
        """
        Register a domain
        """

        domain = data["domain"]
        workflow = [

        ]

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
        parsed_domain
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
