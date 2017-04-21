import logging
from ..models import (
    Registrant,
    ContactType,
    Contact
)

log = logging.getLogger(__name__)


class DomainManager(object):

    """Docstring for DomainManager. """

    def __init__(self, registered_domain):
        """
        manager a registered domain

        :registered_domain: RegisteredDomain

        """
        self._registered_domain = registered_domain

    def manage_update_change(self, chg=None):
        """
        Handle "change" updates to a domain.

        This will include registrant, authcode, (perhaps status)

        :chg: dict containing change fields

        """
        if chg:
            registrant = chg.pop("registrant", None)
            if registrant:
                # Deactivate current DomainRegistrant object
                current_registrants = self._registered_domain.registrant.filter(
                    active=True
                )
                if current_registrants.exists():
                    for current_registrant in current_registrants.all():
                        current_registrant.active = False
                        current_registrant.save()
                self.connect_domain_to_registrant(registrant)

    def manage_update_add(self, add=None):
        """
        Add objects to the domain

        :add: dict with fields to add for.

        """
        if add:
            self.add_domain_contacts(add.pop("contact", None))

    def add_domain_contacts(self, contacts=None):
        """
        Add contacts to the registered domain

        :contacts: list of contacts
        """
        if contacts:
            for item in contacts:
                (con_type, registry_id), = item.items()
                contact_type = ContactType.objects.get(name=con_type)
                contact = Contact.objects.get(registry_id=registry_id)
                self._registered_domain.contacts.create(
                    contact=contact,
                    contact_type=contact_type,
                    active=True
                )
                log.info("Created %s contact %s for %s" % (con_type,
                                                           registry_id,
                                                           str(self._registered_domain)))

    def manage_update_remove(self, rem=None):
        """
        Remove objects that should no longer be associated with the domain

        :rem: dict containing objects to remove

        """
        if rem:
            self.remove_domain_contacts(rem.pop("contact", None))

    def remove_domain_contacts(self, contacts=None):
        """
        Remove contacts from a domain

        :contacts: list of contacts

        """

        if contacts:
            for domain_contact in contacts:
                (contact_type, registry_id), = domain_contact.items()
                contact = self._registered_domain.contacts.get(
                    contact__registry_id=registry_id,
                    contact_type__name=contact_type
                )
                contact.active = False
                contact.save()
                log.info("Deactivated %s contact %s for %s" % (contact_type,
                                                               registry_id,
                                                               str(self._registered_domain)))

    def connect_domain_to_registrant(self, registry_id):
        """
        Connect a domain and a new registrant based on registry id.

        :registry_id: str registry_id
        """

        new_registrant = Registrant.objects.get(
            registry_id=registry_id
        )
        self._registered_domain.registrant.create(
            registrant=new_registrant,
            active=True,
        )

    def update(self, update_data):
        """
        Update a domain using the given data.

        This assumes a successful response has come back from an update domain
        command at a registry.

        :data: TODO
        :returns: TODO

        """
        chg = update_data.pop("chg", None)
        add = update_data.pop("add", None)
        rem = update_data.pop("rem", None)
        self.manage_update_change(chg)
        self.manage_update_remove(rem)
        self.manage_update_add(add)
