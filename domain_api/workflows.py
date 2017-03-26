from __future__ import absolute_import, unicode_literals
from .tasks import (
    check_domain,
    check_bulk_domain,
    create_registrant,
    create_registry_contact,
    create_domain,
    connect_domain,
    check_host,
    create_host,
)
from domain_api.models import (
    DefaultAccountTemplate,
    DefaultAccountContact,
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
        return check_bulk_domain.si(fqdn_list)

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
            provider__slug=self.registry,
            project_id=user
        )
        return default_registrant.account_template.id

    def append_contact_obj_to_workflow(self,
                                       contact,
                                       user_id,
                                       mandatory=False):
        """
        Append DefaultAccountDetail object to create contact workflow.

        :template_id: int id of an AccountDetail object
        """
        contact_type = contact.contact_type.name
        template_id = contact.account_template.id
        user = user_id
        contact_dict = {contact_type: template_id}
        if mandatory:
            user = contact.project_id.id
        self.append_contact_workflow(contact_dict, user)

    def append_contact_workflow(self,
                                contact,
                                user_id):
        """
        Append item to create contact workflow.

        :template_id: int id of an AccountDetail object
        """
        (contact_type, person_id), = contact.items()
        self.workflow.append(
            create_registry_contact.s(
                person_id=person_id,
                registry=self.registry,
                contact_type=contact_type,
                user=user_id
            )
        )

    def create_contact_workflow(self, data, user):
        """
        Append create contact commands to workflow. Preferentially append
        mandatory default contacts if there are any, followed by contacts
        sent in create domain request and finally default non-mandatory
        contacts.

        :data: EPP datastructure

        """
        default_contacts = DefaultAccountContact.objects.filter(
            provider__slug=self.registry
        )
        mandatory_contacts = default_contacts.filter(mandatory=True)
        if mandatory_contacts.exists():
            [self.append_contact_obj_to_workflow(i, user, True) for i in mandatory_contacts.all()]
        elif "contacts" in data:
            [self.append_contact_workflow(i, user) for i in data["contacts"]]
        elif default_contacts.exists():
            [self.append_contact_obj_to_workflow(i, user, False) for i in default_contacts.all()]

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
        log.debug({"default_contact": registrant})
        self.workflow.append(
            create_registrant.si(
                epp,
                person_id=registrant,
                registry=self.registry,
                user=user.id
            )
        )
        self.create_contact_workflow(data, user)

        self.workflow.append(create_domain.s(self.registry))
        self.workflow.append(connect_domain.s())
        return self.workflow

    def create_host(self, data, user):
        """
        Set up workflow for creating a host

        :data: dict create host data
        :user: user object
        :returns: dict response returned by registry

        """
        self.workflow.append(check_host.s(data["host"]))
        self.workflow.append(create_host.s(data))
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
