from __future__ import absolute_import, unicode_literals
from .tasks import (
    check_domain,
    check_bulk_domain,
    create_registrant,
    create_registry_contact,
    create_domain,
    connect_domain
)
from domain_api.models import (
    DefaultAccountTemplate
)
from django_logging import log


class Workflow(object):

    """
    Steps needed for registry operations.
    """

    def __init__(self):
        """
        Initialise workflow object.
        """
        self.workflow = []
        self.registry = None

    def check_domains(self, fqdn_list):
        """
        Create chained workflows for set of domains.

        :fqdn_list: list of fqdns
        :returns: chain object for celery

        """
        return check_bulk_domain.si(self.registry, fqdn_list)

    def fetch_registrant(self, data, user):
        """
        Return either the default registrant or whatever user specified.

        :user: request user
        :data: request data
        :returns: int id of registrant

        """
        if "registrant" in data:
            return data["registrant"]
        default_registrant = DefaultAccountTemplate.objects.get(
            provider=self.registry,
            project_id=user
        )
        return default_registrant.id

    def fetch_contacts(self, data, user):
        """
        Return either set of default contacts for registry or user specified.

        :data: request data
        :user: request user
        :returns: list of contacts

        """
        pass

    def create_domain(self, data, user):
        """
        Set up workflow for creating a domain

        :data: dict for an epp create domain request
        :returns: chain object for celery

        """
        epp = {
            "name": data["domain"]
        }
        if "ns" in data:
            epp["ns"] = data["ns"]

        registrant = self.fetch_registrant(data, user)

        self.workflow.append(check_domain.s(data["domain"]))
        # TODO: process nameservers
        self.workflow.append(
            create_registrant.si(
                epp,
                person_id=registrant,
                registry=self.registry,
                user=user.id
            )
        )
        for contact in data["contacts"]:
            log.debug(contact)
            (contact_type, person_id), = contact.items()
            log.debug({"parsed": {"contact_type": contact_type,
                                  "person": person_id}})
            self.workflow.append(
                create_registry_contact.s(
                    person_id=person_id,
                    registry=self.registry,
                    contact_type=contact_type,
                    user=user.id
                )
            )

        self.workflow.append(create_domain.s(self.registry))
        self.workflow.append(connect_domain.s())
        return self.workflow


class CentralNic(Workflow):

    """
    Registry operations specific for CentralNic
    """

    def __init__(self):
        super().__init__()
        self.registry = 'centralnic-test'


class CoccaTest(Workflow):

    """
    Registry operations specific for Cocca
    """

    def __init__(self):
        super().__init__()
        self.registry = 'cocca-test'


workflow_registries = {
    "centralnic-test": CentralNic,
    "cocca-test": CoccaTest
}


def workflow_factory(registry):
    """
    Return workflow manager for a given registry.


    :registry: str or DomainProvider object
    :returns: A subclass of DomainManager
    """
    return workflow_registries[registry]
