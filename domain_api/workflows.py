from __future__ import absolute_import, unicode_literals
from celery import chain
from ..tasks import (
    check_domain,
    create_registry_contact
)

from .models import TopLevelDomainProvider, TopLevelDomain
from ..utilities.domain import parsed_domain


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
        self.workflow.append(
            create_registry_contact.s(
                registrant,
                registry,
                'registrant'
            )
        )
        contacts = data["contacts"]
        nameservers = data["ns"]






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

class WorkflowFactory(object):

    """
    Define workflows patterns for domain operations.
    """


    @staticmethod
    def get_workflow(self, registry):
        """


        :registry: str or DomainProvider object
        :returns: TODO

        """
        return workflow_registries[registry]





