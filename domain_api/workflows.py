from __future__ import absolute_import, unicode_literals
from ..tasks import (
    check_domain,
    create_registrant,
    create_registry_contact,
    create_domain
)

from .models import TopLevelDomainProvider, TopLevelDomain
from ..utilities.domain import parse_domain


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
        self.workflow.append(check_domain.s(data["domain"], self.registry))
        registrant = data["registrant"]
        # TODO: process nameservers
        epp = {
            "domain": data["domain"],
            "ns": data["ns"]
        }
        self.workflow.append(
            create_registrant.si(
                epp,
                registrant,
                self.registry
            )
        )
        for contact in data["contacts"]:
            for contact_type, person_id in contact.items():
                self.workflow.append(
                    create_registry_contact.s(
                        person_id,
                        self.registry,
                        contact_type
                    )
                )

        self.workflow.append(create_domain.s(self.registry))
        return workflow


class CentralNic(Workflow):

    """
    Registry operations specific for CentralNic
    """

    def __init__(self):
        super().__init__()
        self.registry = 'centralnic-test'



workflow_registries = {
    "centralnic-test": CentralNic
}

def workflow_factory(self, registry):
    """
    Return workflow manager for a given registry.


    :registry: str or DomainProvider object
    :returns: A subclass of DomainManager
    """
    return workflow_registries[registry]
