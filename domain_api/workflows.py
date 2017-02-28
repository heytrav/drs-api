from __future__ import absolute_import, unicode_literals
from .tasks import (
    check_domain,
    create_registrant,
    create_registry_contact,
    create_domain,
    connect_domain
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

    def create_domain(self, data):
        """
        Set up workflow for creating a domain

        :data: dict for an epp create domain request
        :returns: chain object for celery

        """
        epp = {
            "name": data["domain"],
            "ns": data["ns"]
        }
        self.workflow.append(check_domain.s(data["domain"]))
        # TODO: process nameservers
        self.workflow.append(
            create_registrant.si(
                epp,
                person_id=data["registrant"],
                registry=self.registry
            )
        )
        for contact in data["contacts"]:
            log.debug(contact)
            (contact_type, person_id), = contact.items()
            log.debug({"parsed": {"contact_type": contact_type,
                                  "person": person_id}})
            self.workflow.append(
                create_registry_contact.s(
                    person_id,
                    self.registry,
                    contact_type
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
