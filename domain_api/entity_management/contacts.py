import uuid
from itertools import chain
from django_logging import log
from domain_api.epp.actions.contact import Contact as ContactAction
from ..models import Contact, Registrant


class ContactFactory(object):

    """
    Create a registrant or contact handle at a registry.

    This should help abstract creating either type of contact to avoid code
    duplication.
    """

    contact_fields = ('telephone', 'fax', 'email')
    disclose_fields = ('disclose_name', 'disclose_company', 'disclose_address',
                       'disclose_telephone', 'disclose_fax', 'disclose_email')
    postal_info_fields = ('name', 'company',)
    address_fields = ('city', 'state', 'postcode', 'country')
    street_fields = ('street1', 'street2', 'street3')

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
        if not template.disclose_address:
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

    def process_postal_info_change(self, data):
        """
        Process data that goes into postalInfo section of update contact
        request.

        :data: dict postal info data
        :returns: dict with postal_info fields or None
        """
        contact = self.contact_object
        if any(k in data for k in chain(self.postal_info_fields,
                                        self.address_fields,
                                        self.street_fields)):
            postal_info = {"type": contact.postal_info_type}
            field_mappings = {"name": "name", "company": "org"}

            if any(k in data for k in field_mappings.keys()):
                for (key, value) in field_mappings.items():
                    if key in data:
                        postal_info[value] = data[key]

            if any(k in data for k in self.address_fields):
                address = {
                    "city": data.get('city', contact.city),
                    "cc": data.get('country', contact.country)
                }
                if any(k in data for k in self.street_fields):
                    address["street"][0] = data.get('street1', contact.street1)
                    address["street"][1] = data.get('street2', contact.street2)
                    address["street"][2] = data.get('street3', contact.street3)
                if "state" in data:
                    address["sp"] = data["state"]
                if "postcode" in data:
                    address["pc"] = data["postcode"]

                postal_info["addr"] = address
            return postal_info
        return None

    def process_disclose_change(self, data):
        """
        Process change to "disclose" info for a contact.

        :data: dict with update data
        :returns: dict with appropriate disclose changes

        """
        if any(k in data for k in self.disclose_fields):
            contact = self.contact_object
            non_disclose = []
            if not data.get("disclose_name", contact.disclose_name):
                non_disclose.append(
                    {
                        "name": "name",
                        "type": contact.postal_info_type
                    }
                )
            if not data.get("disclose_company", contact.disclose_company):
                non_disclose.append(
                    {
                        "name": "org",
                        "type": contact.postal_info_type
                    }
                )
            if not data.get("disclose_address", contact.disclose_address):
                non_disclose.append(
                    {
                        "name": "addr",
                        "type": contact.postal_info_type
                    }
                )
            if not data.get("disclose_telephone", contact.disclose_telephone):
                non_disclose.append("voice")
            if not data.get("disclose_fax", contact.disclose_fax):
                non_disclose.append("fax")
            if not data.get("disclose_email", contact.disclose_email):
                non_disclose.append("email")
            return non_disclose
        return None

    def process_contact_change(self, data):
        """
        Process data that goes into "chg" part of update contact request.

        :data: dict containing update data
        :returns: dict for "chg" field in update contact.

        """
        if any(k in data for k in chain(self.contact_fields,
                                        self.disclose_fields,
                                        self.postal_info_fields,
                                        self.address_fields,
                                        self.street_fields)):
            change = {}
            postal_info_change = self.process_postal_info_change(data)

            if postal_info_change:
                change["postalInfo"] = postal_info_change
            if "telephone" in data:
                change["voice"] = data["telephone"]
            if "fax" in data:
                change["fax"] = data["fax"]
            if "email" in data:
                change["email"] = data["email"]

            non_disclose = self.process_disclose_change(data)
            if non_disclose:
                change["disclose"] = {
                    "flag": 0,
                    "disclosing": non_disclose
                }

            return change
        return None

    def process_update_add_or_remove(self, data):
        """
        Process field items that are to be added

        :data: dict with contact data to update
        :returns: dict with "add" and "rem" parts of update

        """
        if "status" in data:
            delta = {}
            add = []
            rem = []
            current_status = self.contact_object.status
            if not current_status:
                current_status = ""
            stati = current_status.split(';')
            new_stati = data["status"].split(';')
            for new_status in new_stati:
                if new_status and new_status not in stati:
                    add.append(new_status)
            for old_status in stati:
                if old_status and old_status not in new_stati:
                    rem.append(old_status)
            if len(add) > 0:
                delta["add"] = add
            if len(rem) > 0:
                delta["rem"] = rem
            if "add" in delta or "rem" in delta:
                return delta
        return None


    def update_contact(self, data):
        """
        Send an update contact command to the registry.

        :data: contact data to update
        :returns: EPP response

        """
        change = self.process_contact_change(data)
        delta = self.process_update_add_or_remove(data)
        update_data = {"id": self.contact_object.registry_id}
        if change:
            update_data["chg"] = change
        if delta:
            update_data.update(delta)

        log.info(update_data)
        contact = ContactAction()
        response = contact.update(self.provider.slug, update_data)
        log.debug(response)
        return response



class RegistrantManager(ContactFactory):

    """
    Manage registrant creation.
    """

    def __init__(self,
                 registrant=None,
                 provider=None,
                 template=None,
                 user=None):
        """
        Initialise factory.
        """
        if registrant:
            self.contact_object = Registrant.objects.get(registry_id=registrant)
            super().__init__(
                provider=self.contact_object.provider,
                user=self.contact_object.project_id
            )
        else:
            super().__init__(
                provider=provider,
                template=template,
                user=user
            )
            self.related_contact_set = Registrant.objects.filter(
                domainregistrant__active=True,
                account_template=template,
                provider__slug=provider
            ).distinct()


class ContactManager(ContactFactory):

    """
    Manage contact creation.
    """

    def __init__(self,
                 contact=None,
                 provider=None,
                 template=None,
                 contact_type=None,
                 user=None):
        """
        Initialise factory.
        """
        if contact:
            self.contact_object = Contact.objects.get(registry_id=contact)
            super().__init__(
                provider=self.contact_object.provider,
                user=self.contact_object.project_id
            )
        else:
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
