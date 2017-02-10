from django_logging import log
from ..models import ContactHandle, RegistrantHandle
from ..serializers import ContactHandleSerializer, RegistrantHandleSerializer
from domain_api.epp.actions.contact import Contact


class ContactHandleFactory(object):

    """
    Create a registrant or contact handle at a registry.

    This should help abstract creating either type of contact to avoid code
    duplication.
    """

    def __init__(self,
                 provider=None,
                 contact_type="contact",
                 context=None):
        """
        Initialise factory.
        """
        self.provider = provider
        self.contact_type = contact_type
        self.context = context

    def process_handle(self, handle, person):
        """
        Return correct type of serializer for contact type.

        :handle: Handle for contact
        :person: PersonalDetail object to link to new handle
        :returns: registrant or contact handle object

        """
        if self.contact_type == "contact":
            contact_handle = person.contacthandle_set.create(
                handle=handle,
                provider=self.provider
            )
            return ContactHandleSerializer(
                contact_handle,
                context=self.context
            )
        elif self.contact_type == "registrant":
            contact_handle = person.registranthandle_set.create(
                handle=handle,
                provider=self.provider
            )
            return RegistrantHandleSerializer(
                contact_handle,
                context=self.context
            )
        raise Exception("No matching serializer for contact type.")

    def get_handle_id(self):
        """
        Return a generic handle string.
        :returns: string

        """
        obj_id = 0
        if self.contact_type == "contact":
            obj_id = ContactHandle.objects.count() + 1
        elif self.contact_type == "registrant":
            obj_id = RegistrantHandle.objects.count() + 1

        return "-".join([self.provider.slug[:3], self.contact_type[:3], str(obj_id)])

    def create_registry_contact(self, person):
        """
        Create contact at registry and add to registrant handle or
        contact handle.

        :person: PersonalDetail object
        :returns: serializer object

        """
        handle = self.get_handle_id()
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
        return self.process_handle(handle, person)
