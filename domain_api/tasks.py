from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django_logging import log, ErrorLogObject
from .models import (
    ContactHandle,
    DomainProvider
)
from .entity_management.contacts import ContactHandleFactory
from .epp.actions.domain import Domain as DomainAction
from .epp.queries import Domain

@shared_task
def check_domain(domain, registry):
    """
    Check if a domain exists.

    :domain: FQDN to check
    :returns: boolean

    """
    log.info({"command": "check_domain",
              "domain": domain,
              "registry": registry})
    query = Domain()
    availability = query.check_domain(registry, domain)
    available = availability["result"][0]["available"]
    if available:
        return available
    raise Exception("Domain not available")

@shared_task
def create_registrant(epp, person_id=None, registry=None, force=False):
    """
    Create a new contact at a registry. If a contact handle matching the
    person id and the registry already exists, use that one.

    :person_id: Integer identifying a person
    :registry: Registry slug to identify registry
    :force: Boolean value
    :returns: registry id of new contact.

    """
    log.info({"command": "create_contact",
              "epp": epp,
              "person": person_id,
              "registry": registry,
              "contact_type": contact_type})
    provider = DomainProvider.objects.get(slug=registry)
    person = PersonalDetail.objects.get(pk=person_id)
    contact_manager = ContactHandleFactory(provider, person, 'registrant')
    contact_handle = contact_manager.fetch_existing_handle()
    if not contact_handle or force:
        contact_handle = contact_manager.create_registry_contact()
    epp["registrant"] = contact_handle.handle
    return epp


@shared_task
def create_registry_contact(epp, person_id=None, registry=None, contact_type="contact", force=False):
    """
    Create a new contact at a registry. If a contact handle matching the
    person id and the registry already exists, use that one.

    :person_id: Integer identifying a person
    :registry: Registry slug to identify registry
    :force: Boolean value
    :returns: registry id of new contact.

    """
    log.info(
        {
            "command": "create_registry_contact",
            "epp": epp,
            "person": person_id,
            "registry": registry,
            "contact_type": contact_type
        }
    )
    contacts = epp.get("contacts", [])

    log.info({"command": "create_contact",
              "person": person_id,
              "registry": registry,
              "contact_type": contact_type})
    provider = DomainProvider.objects.get(slug=registry)
    person = PersonalDetail.objects.get(pk=person_id)
    contact_manager = ContactHandleFactory(provider, person, 'contact')
    contact_handle = contact_manager.fetch_existing_handle()
    if not contact_handle or force:
        contact_handle = contact_manager.create_registry_contact()
    contact = {}
    contact[contact_type] = contact_handle
    contacts.append(contact)
    epp["contacts"] = contacts
    return epp


@shared_task
def create_domain(epp, registry):
    """
    Create a domain at a given registry

    :epp: raw epp command
    :returns: success or fail

    """
    log.info(
        {
            "command": "create_domain",
            "epp": epp,
            "registry": registry,
        }
    )
    domain = DomainAction()
    result = domain.create(epp, registry)
    return result
