import uuid
from itertools import chain
import logging
from domain_api.epp.actions.contact import Contact as ContactAction
from ..models import Contact, Registrant

log = logging.getLogger(__name__)


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
    contact_model = Contact

    def __init__(self,
                 contact=None,
                 provider=None,
                 template=None,
                 user=None):
        """
        Initialise factory.
        """
        self.provider = provider
        self.template = template
        self.user = user
        if contact:
            log.info("Creating manager with related_contact_set")
            self.contact_object = self.contact_model.objects.get(
                registry_id=contact
            )
            self.provider = self.contact_object.provider
            self.user = self.contact_object.project_id

        if self.template:
            self.related_contact_set = self.contact_model.objects.filter(
                domaincontact__active=True,
                account_template=template,
                domaincontact__contact_type__name=contact_type,
                provider=provider
            ).distinct()

    def fetch_existing_contact(self):
        """
        Check if the template has an existing handle at a provider and return it
        if it does.
        :returns: str registry handle

        """
        if self.related_contact_set.count() > 0:
            return self.related_contact_set.first()
        log.info("Did not find an existing contact.")
        return None

    def create_local_contact(self, eppdata):
        """
        Return correct type of serializer for contact type.

        :eppdata: Handle for contact
        :template: AccountDetail object to link to new handle
        :returns: registrant or contact handle object

        """
        registry_id = eppdata["id"]
        log.debug("user=%s" % self.user.id)
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
        contact_id = self.get_registry_id()
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
            "id": contact_id,
            "voice": template.telephone,
            "fax": template.fax,
            "email": template.email,
            "postalInfo": postal_info
        }
        if non_disclose:
            contact_info["disclose"] = {"flag": 0, "disclosing": non_disclose}
        contact = ContactAction()
        registry = self.provider.slug
        response = contact.create(registry, contact_info)
        log.info("Created contact=%s at registry=%s" % (contact_id, registry))
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
                    address["street"] = []
                    street1 = data.get('street1', contact.street1)
                    street2 = data.get('street2', contact.street2)
                    street3 = data.get('street3', contact.street3)
                    address["street"].append(street1)
                    if street2:
                        address["street"].append(street2)
                    if street3:
                        address["street"].append(street3)
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
            pro_disclose = []
            if "disclose_name" in data and data["disclose_name"] != contact.disclose_name:
                change_data = {
                    "name": "name",
                    "type": contact.postal_info_type
                }
                if data["disclose_name"]:
                    pro_disclose.append(change_data)
                else:
                    non_disclose.append(change_data)
            if "disclose_company" in data and data["disclose_company"] != contact.disclose_company:
                change_data = {
                    "name": "org",
                    "type": contact.postal_info_type
                }
                if data["disclose_company"]:
                    pro_disclose.append(change_data)
                else:
                    non_disclose.append(change_data)
            if "disclose_address" in data and data["disclose_address"] != contact.disclose_address:
                change_data = {
                    "name": "addr",
                    "type": contact.postal_info_type
                }
                if data["disclose_address"]:
                    pro_disclose.append(change_data)
                else:
                    non_disclose.append(change_data)
            if "disclose_telephone" in data and data["disclose_telephone"] != contact.disclose_telephone:
                if data["disclose_telephone"]:
                    pro_disclose.append("voice")
                else:
                    non_disclose.append("voice")
            if "disclose_fax" in data and data["disclose_fax"] != contact.disclose_fax:
                if data["disclose_fax"]:
                    pro_disclose.append("fax")
                else:
                    non_disclose.append("fax")
            if "disclose_email" in data and data["disclose_email"] != contact.disclose_email:
                if data["disclose_email"]:
                    pro_disclose.append("email")
                else:
                    non_disclose.append("email")
            if len(pro_disclose) >= len(non_disclose):
                return (pro_disclose, 1)
            return (non_disclose, 0)
        return (None, None)

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

            disclose_set, flag = self.process_disclose_change(data)
            if disclose_set:
                change["disclose"] = {
                    "flag": flag,
                    "disclosing": disclose_set
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
        log.debug("Received response")
        return response


class RegistrantManager(ContactFactory):

    """
    Manage registrant creation.
    """

    contact_model = Registrant


class ContactManager(ContactFactory):

    """
    Manage contact creation.
    """

    pass
