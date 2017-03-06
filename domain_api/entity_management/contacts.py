import uuid
from django_logging import log
from domain_api.epp.actions.contact import Contact as ContactAction


class ContactFactory(object):

    """
    Create a registrant or contact handle at a registry.

    This should help abstract creating either type of contact to avoid code
    duplication.
    """

    def __init__(self,
                 provider=None,
                 person=None,
                 user=None):
        """
        Initialise factory.
        """
        self.provider = provider
        self.person = person
        self.user = user

    def fetch_existing_contact(self):
        """
        Check if the person has an existing handle at a provider and return it
        if it does.
        :returns: str registry handle

        """
        if self.related_contact_set.count() > 0:
            return self.related_contact_set.first()
        return None

    def create_local_contact(self, eppdata):
        """
        Return correct type of serializer for contact type.

        :eppdata: Handle for contact
        :person: AccountDetail object to link to new handle
        :returns: registrant or contact handle object

        """
        registry_id = eppdata["id"]
        contact = self.related_contact_set.create(
            registry_id=registry_id,
            provider=self.provider,
            project_id=self.user
        )
        return contact

    def get_registry_id(self):
        """
        Return a generic handle string.
        :returns: string

        """
        return str(uuid.uuid4())[:8]

    def process_disclose(self):
        """
        Process disclose fields and flag attributes the user does not want
        to disclose.

        :returns: dict with non-disclose element.

        """
        person = self.person
        postal_info_type = person.postal_info_type
        non_disclose = []
        if not person.disclose_name:
            non_disclose.append({"name": "name", "type": postal_info_type})
        if not person.disclose_company:
            non_disclose.append({"name": "org", "type": postal_info_type})
        if not person.disclose_company:
            non_disclose.append({"name": "addr", "type": postal_info_type})
        if not person.disclose_telephone:
            non_disclose.append("voice")
        if not person.disclose_email:
            non_disclose.append("email")
        if not person.disclose_fax:
            non_disclose.append("fax")
        log.debug(non_disclose)
        if len(non_disclose) > 0:
            return non_disclose
        return None

    def create_registry_contact(self):
        """
        Create contact at registry and add to registrant handle or
        contact handle.

        :person: AccountDetail object
        :returns: serializer object

        """
        contact = self.get_registry_id()
        person = self.person
        street = [person.street1]
        if person.street2 != "":
            street.append(person.street2)
        if person.street3 != "":
            street.append(person.street3)
        non_disclose = self.process_disclose()
        company = ""
        if person.company:
            company = person.company

        postal_info = {
            "name": person.first_name + " " + person.surname,
            "org": company,
            "type": person.postal_info_type,
            "addr": {
                "street": street,
                "city": person.city,
                "sp": person.state,
                "pc": person.postcode,
                "cc": person.country
            }
        }
        contact_info = {
            "id": contact,
            "voice": person.telephone,
            "fax": person.fax,
            "email": person.email,
            "postalInfo": postal_info
        }
        if non_disclose:
            contact_info["disclose"] = {"flag": 0, "disclosing": non_disclose}
        log.info(contact_info)
        contact = ContactAction()
        response = contact.create(self.provider.slug, contact_info)
        log.info(response)
        return self.create_local_contact(response)


class RegistrantManager(ContactFactory):

    """
    Manage registrant creation.
    """

    def __init__(self,
                 provider=None,
                 person=None,
                 user=None):
        """
        Initialise factory.
        """
        super().__init__(
            provider=provider,
            person=person,
            user=user
        )
        self.related_contact_set = user.registrants.filter(
            provider=provider
        )


class ContactManager(ContactFactory):

    """
    Manage contact creation.
    """

    def __init__(self,
                 provider=None,
                 person=None,
                 user=None):
        """
        Initialise factory.
        """
        super().__init__(
            provider=provider,
            person=person,
            user=user
        )
        self.related_contact_set = user.contacts.filter(
            provider=provider
        )
