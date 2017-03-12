import uuid
from django_logging import log
from domain_api.epp.actions.contact import Contact as ContactAction
from ..models import Contact, Registrant


class ContactFactory(object):

    """
    Create a registrant or contact handle at a registry.

    This should help abstract creating either type of contact to avoid code
    duplication.
    """

    def __init__(self,
                 provider=None,
                 template=None,
                 user=None):
        """
        Initialise factory.
        """
        self.provider = provider
        self.template = template
        self.user = user

    def fetch_existing_contact(self):
        """
        Check if the template has an existing handle at a provider and return it
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
        :template: AccountDetail object to link to new handle
        :returns: registrant or contact handle object

        """
        registry_id = eppdata["id"]
        log.debug({"user": self.user.id})
        contact = self.related_contact_set.create(
            registry_id=registry_id,
            provider=self.provider,
            project_id=self.user,
            account_template=self.template
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
        template = self.template
        postal_info_type = template.postal_info_type
        non_disclose = []
        if not template.disclose_name:
            non_disclose.append({"name": "name", "type": postal_info_type})
        if not template.disclose_company:
            non_disclose.append({"name": "org", "type": postal_info_type})
        if not template.disclose_company:
            non_disclose.append({"name": "addr", "type": postal_info_type})
        if not template.disclose_telephone:
            non_disclose.append("voice")
        if not template.disclose_fax:
            non_disclose.append("fax")
        if not template.disclose_email:
            non_disclose.append("email")
        log.debug({"nondisclose": non_disclose})
        if len(non_disclose) > 0:
            return non_disclose
        return None

    def create_registry_contact(self):
        """
        Create contact at registry and add to registrant handle or
        contact handle.

        :template: AccountDetail object
        :returns: serializer object

        """
        contact = self.get_registry_id()
        template = self.template
        street = [template.street1]
        if template.street2 != "":
            street.append(template.street2)
        if template.street3 != "":
            street.append(template.street3)
        non_disclose = self.process_disclose()
        company = ""
        if template.company:
            company = template.company

        postal_info = {
            "name": template.first_name + " " + template.surname,
            "org": company,
            "type": template.postal_info_type,
            "addr": {
                "street": street,
                "city": template.city,
                "sp": template.state,
                "pc": template.postcode,
                "cc": template.country
            }
        }
        contact_info = {
            "id": contact,
            "voice": template.telephone,
            "fax": template.fax,
            "email": template.email,
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
                 template=None,
                 user=None):
        """
        Initialise factory.
        """
        super().__init__(
            provider=provider,
            template=template,
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
                 template=None,
                 contact_type=None,
                 user=None):
        """
        Initialise factory.
        """
        super().__init__(
            provider=provider,
            template=template,
            user=user
        )
        self.related_contact_set = Contact.objects.filter(
            domaincontact__active=True,
            account_template=template,
            domaincontact__contact_type__name=contact_type,
            provider__slug=provider
        ).distinct()
