from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django_logging import log, ErrorLogObject
from .models import (
    Contact,
    ContactType,
    Domain,
    DomainContact,
    DomainProvider,
    DomainRegistrant,
    PersonalDetail,
    RegisteredDomain,
    Registrant,
    TopLevelDomain,
    TopLevelDomainProvider
)
from .entity_management.contacts import ContactFactory
from .epp.actions.domain import Domain as DomainAction
from .epp.queries import Domain as DomainQuery
from .utilities.domain import parse_domain

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
    query = DomainQuery()
    availability = query.check_domain(registry, domain)
    available = availability["result"][0]["available"]
    log.info({"available": available})
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
    try:
        provider = DomainProvider.objects.get(slug=registry)
        person = PersonalDetail.objects.get(pk=person_id)
        contact_manager = ContactFactory(provider, person, 'registrant')
        contact = contact_manager.fetch_existing_contact()
        if not contact or force:
            contact = contact_manager.create_registry_contact()
        epp["registrant"] = contact.registry_id
    except Exception as e:
        log.error({"error": e})
        raise e
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
    contacts = epp.get("contact", [])

    provider = DomainProvider.objects.get(slug=registry)
    person = PersonalDetail.objects.get(pk=person_id)
    contact_manager = ContactFactory(provider, person, 'contact')
    contact_obj = contact_manager.fetch_existing_contact()
    if not contact_obj or force:
        contact_obj = contact_manager.create_registry_contact()

    log.info({"contact_handle": contact_obj.registry_id})
    contact = {}
    contact[contact_type] = contact_obj.registry_id
    contacts.append(contact)
    epp["contact"] = contacts
    return epp


@shared_task
def create_domain(epp, registry):
    """
    Create a domain at a given registry

    :epp: raw epp command
    :returns: success or fail

    """
    try:
        domain = DomainAction()
        result = domain.create(registry, epp)
        return {**epp, **result}
    except Exception as e:
        log.error({"error": e})
        raise e

@shared_task
def connect_domain(create_data):
    """
    Connect the newly created domain in our database.

    :create_data: The epp request and response information
    :returns: TODO

    """
    try:
        parsed_domain = parse_domain(create_data["name"])
        domain_obj, _ = Domain.objects.get_or_create(
            name=parsed_domain["domain"],
            idn=parsed_domain["domain"]
        )
        tld_provider = TopLevelDomainProvider.objects.get(
            zone=parsed_domain["zone"]
        )
        registered_domain = RegisteredDomain(
            domain=domain_obj,
            tld=parsed_domain["zone"],
            tld_provider=tld_provider,
            registration_period=1,
            anniversary=create_data["expiration_date"],
            created=create_data["create_date"],
            active=True
        )
        registered_domain.save()
        registrant = Registrant.objects.get(registry_id=create_data["registrant"])
        registered_domain.registrant.create(
            registrant=registrant,
            active=True,
        )
        for item in create_data["contact"]:
            (con_type, registry_id), = item.items()
            contact_type = ContactType.objects.get(name=con_type)
            contact = Contact.objects.get(registry_id=registry_id)
            registered_domain.contacts.create(
                contact=contact,
                contact_type=contact_type,
                active=True
            )
        return create_data
    except Exception as e:
        log.error({"error": e})
