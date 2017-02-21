from django_logging import log
from ..models import Contact, Registrant
from domain_api.epp.actions.contact import Contact


class ContactFactory(object):

    """
    Create a registrant or contact handle at a registry.

    This should help abstract creating either type of contact to avoid code
    duplication.
    """

    def __init__(self,
                 provider=None,
                 person=None,
                 contact_type="contact",
                 context=None):
        """
        Initialise factory.
        """
        self.provider = provider
        self.context = context
        self.person = person
        self.contact_type = contact_type
        if contact_type == 'contact':
            self.related_handle_set = person.contacthandle_set
        elif contact_type == 'registrant':
            self.related_handle_set = person.registranthandle_set

    def fetch_existing_handle(self):
        """
        Check if the person has an existing handle at a provider and return it
        if it does.
        :returns: str registry handle

        """
        if self.related_handle_set.count() > 0:
            return self.related_handle_set.first()
        return None

    def create_local_handle(self, eppdata):
        """
        Return correct type of serializer for contact type.

        :eppdata: Handle for contact
        :person: PersonalDetail object to link to new handle
        :returns: registrant or contact handle object

        """
        handle = eppdata["id"]
        contact_handle = self.related_handle_set.create(
            handle=handle,
            provider=self.provider
        )
        return contact_handle

    def get_handle_id(self):
        """
        Return a generic handle string.
        :returns: string

        """
        obj_id = None
        if self.contact_type == "contact":
            obj_id = Contact.objects.count() + 1
        elif self.contact_type == "registrant":
            obj_id = Registrant.objects.count() + 1

        return "-".join([self.provider.slug[:3], self.contact_type[:3],
                         str(obj_id)])

    def create_registry_contact(self):
        """
        Create contact at registry and add to registrant handle or
        contact handle.

        :person: PersonalDetail object
        :returns: serializer object

        """
        handle = self.get_handle_id()
        person = self.person
        street = [person.street1, person.street2, person.street3]
        postal_info = {
            "name": person.first_name + " " + person.surname,
            "org": person.company,
            "type": "int",
            "addr": {
                "street": street,
                "city": person.city,
                "sp": person.state,
                "pc": person.postcode,
                "cc": person.country
            }
        }
        contact_info = {
            "id": handle,
            "voice": person.telephone,
            "fax": person.fax,
            "email": person.email,
            "postalInfo": postal_info
        }
        contact = Contact()
        response = contact.create(self.provider.slug, contact_info)
        log.info(response)
        return self.create_local_handle(response)
