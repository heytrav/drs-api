from __future__ import absolute_import, unicode_literals
import idna
from .tasks import (
    check_domain,
    check_bulk_domain,
    create_registrant,
    create_registry_contact,
    update_domain_registrant,
    update_domain_registry_contact,
    create_domain,
    connect_domain,
    check_host,
    create_host,
    connect_host,
    update_domain,
    local_update_domain,
    init_update_domain,
)
from application.settings import get_logzio_sender
from .models import (
    AccountDetail,
    DefaultAccountTemplate,
    DefaultAccountContact,
    Registrant,
    Contact,
)
import logging

log = logging.getLogger(__name__)


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

    def append(self, callback):
        """
        Append a callback to the internal workflow

        :callback: function

        """
        self.workflow.append(callback)

    def check_domains(self, fqdn_list):
        """
        Create chained workflows for set of domains.

        :fqdn_list: list of fqdns
        :returns: chain object for celery

        """
        return check_bulk_domain.si(fqdn_list)

    def fetch_registrant(self, data, user):
        """
        Return account_detail for either the default registrant or
        whatever user specified.

        :user: request user
        :data: request data
        :returns: int id of registrant

        """
        if "registrant" in data:
            return data["registrant"]
        default_registrant_set = AccountDetail.objects.filter(
            default_registrant=True,
            project_id=user
        )
        if default_registrant_set.exists():
            return default_registrant_set.first().id
        default_registrant = DefaultAccountTemplate.objects.get(
            provider__slug=self.registry,
            project_id=user
        )
        return default_registrant.account_template.id

    def append_contact_obj_to_workflow(self,
                                       contact,
                                       user_obj,
                                       mandatory=False):
        """
        Append DefaultAccountDetail object to create contact workflow.

        :template_id: int id of an AccountDetail object
        """
        contact_type = contact.contact_type.name
        template_id = contact.account_template.id
        user = user_obj.id
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
        self.append(
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
            [self.append_contact_obj_to_workflow(i, user, True)
                for i in mandatory_contacts.all()]
        elif "contacts" in data:
            [self.append_contact_workflow(i, user.id) for i in data["contacts"]]
        elif default_contacts.exists():
            [self.append_contact_obj_to_workflow(i, user, False)
             for i in default_contacts.all()]

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

        if "period" in data:
            epp["period"] = data["period"]
        registrant = self.fetch_registrant(data, user)

        self.append(check_domain.s(data["domain"]))
        log.debug({"default_contact": registrant})
        self.append(
            create_registrant.si(
                epp,
                person_id=registrant,
                registry=self.registry,
                user=user.id
            )
        )
        self.create_contact_workflow(data, user)

        self.append(create_domain.s(self.registry))
        self.append(connect_domain.s())
        return self.workflow

    def check_add_contacts(self, contact_set, current_contacts, epp, user):
        """
        Check set of contacts attached to domain to see what is being added.


        :contact_set: Set of contacts in request
        :current_contacts: contacts currently attached to domain
        :returns: TODO

        """
        for contact in contact_set:
            self.process_add_contact(
                contact,
                current_contacts,
                epp,
                user
            )

    def check_remove_contacts(self, contact_set, current_contacts, epp, user):
        """
        Check set of contacts attached to domain to see what is being removed.

        :contact_set: TODO
        :current_contacts: TODO
        :epp: TODO
        :user: TODO
        :returns: TODO

        """
        for contact in current_contacts.all():
            registry_id = contact.contact.registry_id
            account_template_id = contact.contact.account_template.id
            contact_type = contact.contact_type.name
            check_acct_id = {contact_type: account_template_id}
            is_acct_id = check_acct_id in contact_set
            check_registry_id = {contact_type: registry_id}
            is_reg_id = check_registry_id in contact_set
            if not any([is_acct_id, is_reg_id]):
                rem = epp.get("rem", {})
                contact = rem.get("contact", [])
                contact.append(check_registry_id)
                rem["contact"] = contact
                epp["rem"] = rem

    def check_update_domain_contacts(self, contact_set, epp, domain, user):
        """
        Compare submitted contacts with current set attached to domain.

        :contact_set: list of dict objects with new contact handlers
        :epp: dict EPP request structure
        :domain: RegisteredDomain object
        :user: HTTP request user
        """
        current_contacts = domain.contacts.filter(
            active=True
        )
        self.check_add_contacts(contact_set, current_contacts, epp, user)
        self.check_remove_contacts(contact_set, current_contacts, epp, user)

    def _is_account_detail(self, test_id, user):
        """
        Test whether or not an id is an account detail

        :test_id: str id
        :returns: AccountDetail object

        """
        # Intentionally causes an error if the contact_id isn't an integer.
        account_template_id = int(test_id)
        # Cause an error if the submitted account template id
        # does not belong to requesting user.
        return AccountDetail.objects.get(
            pk=account_template_id,
            project_id=user
        )

    def process_add_contact(self,
                            contact,
                            current_contacts,
                            epp,
                            user):
        """
        Prepare to create a new contact to be added
        """
        (contact_type, contact_id), = contact.items()
        # TODO: this code might introduce a loophole around "mandatory"
        # contacts.
        try:
            account_template = self._is_account_detail(contact_id, user)
            contact_in_set = current_contacts.filter(
                contact_type__name=contact_type,
                contact__account_template=account_template,
            )
            if not contact_in_set.exists():
                # No instance of {<contact_type>: <account_template_id>}
                # exists.  We must create a new contact to update this domain.
                self.append(
                    update_domain_registry_contact.s(
                        person_id=account_template.id,
                        registry=self.registry,
                        contact_type=contact_type,
                        user=user.id
                    )
                )
            return
        except AccountDetail.DoesNotExist as e:
            log.error(str(e))
            return
        except ValueError:
            log.warning(
                "%s not an account detail id; checking registryid" % contact_id
            )

        log.debug("Checking for contact " + contact_id)
        add = epp.get("add", {})
        contacts = add.get("contact", [])
        query_set = Contact.objects.filter(
            provider__slug=self.registry,
        )
        if not user.groups.filter(name='admin').exists():
            query_set = query_set.filter(project_id=user)
        contact_query_set = query_set.filter(registry_id=contact_id)
        # This contact exists
        if contact_query_set.exists():
            # Contact is not already a current contact
            current_contact_instance = current_contacts.filter(
                contact__registry_id=contact_id,
                contact_type__name=contact_type
            )
            if not current_contact_instance.exists():
                new_contact = {}
                new_contact[contact_type] = contact_id
                contacts.append(new_contact)
                add["contact"] = contacts
                epp["add"] = add
                return
            log.warning(
                "Contact %s already exists for this domain" % contact_id
            )
            return
        log.warning("Contact %s does not exist for user " % user.id)
        return

    def check_update_domain_registrant(self, new_registrant, epp, domain, user):
        """
        Given a domain and registrant id or template id, figure out if we're
        creating a new registrant or reusing an existing one.

        :new_registrant: string or int representing an account_detail or
                            registrant
        :epp: Datastructure of EPP command
        :domain: registered domain object
        :user: User object from http request
        """
        current_registrant = domain.registrant.filter(
            active=True
        ).first().registrant
        current_account_detail = current_registrant.account_template.id
        try:
            account_detail = self._is_account_detail(new_registrant, user)
            if current_account_detail != account_detail.id:
                # Add create contact command to workflow
                self.append(
                    update_domain_registrant.s(
                        person_id=account_detail.id,
                        registry=self.registry,
                        user=user.id
                    )
                )
            return
        except AccountDetail.DoesNotExist:
            log.warning("Account detail does not exist for this user")
            get_logzio_sender().append(
                {
                    "message": "Account detail does not exist for this user",
                    "registrant": new_registrant,
                    "user": user,
                    "domain": str(domain)
                }
            )
        except ValueError:
            log.warning(
                "%s not an account detail id;"
                "checking registryid" % new_registrant
            )

        # Look for an existing registrant that belongs to this request user.
        # This assumes that the new registrant id is a "registry id".
        query_set = Registrant.objects.all()
        if not user.groups.filter(name='admin').exists():
            query_set = Registrant.objects.filter(project_id=user)
        registrant_query_set = query_set.filter(
            registry_id=new_registrant
        )

        # Selected registrant exists and belongs to request.user
        if registrant_query_set.exists():
            # Should throw an error if new registrant does not belong to user.
            found_registrant = registrant_query_set.get(
                registry_id=new_registrant
            )
            # The two are not equal so make change
            if current_registrant != found_registrant:
                if "chg" not in epp:
                    epp["chg"] = {}
                epp["chg"]["registrant"] = new_registrant

    def check_update_domain_nameservers(self, ns, epp, domain, user):
        """
        Given a domain and a set of nameservers, determine if some are to be
        added or removed.

        :ns: list of nameservers
        :epp: dict EPP data structure
        :domain: RegisteredDomain object
        :user: HTTP Request user

        """
        current_nameservers = domain.ns.all()
        for ns_host in ns:
            idn = idna.encode(ns_host, uts46=True).decode('ascii')
            if not current_nameservers.filter(idn_host=idn).exists():
                add = epp.get("add", {})
                add_ns = add.get("ns", [])
                add_ns.append(idn)
                add["ns"] = add_ns
                epp["add"] = add
            else:
                log.debug("%s is a current nameserver" % idn)

        for ns_host in current_nameservers:
            idn_included = ns_host.idn_host in ns
            host_included = ns_host.host in ns
            if not any([idn_included, host_included]):
                rem = epp.get("rem", {})
                rem_ns = rem.get("ns", [])
                rem_ns.append(ns_host.idn_host)
                rem["ns"] = rem_ns
                epp["rem"] = rem
            else:
                log.debug("Not removing %s" % ns_host.idn_host)

    def update_domain(self, data, domain, user):
        """Set up workflow for updating a domain

        :data: dict for an epp update domain request
        :domain: registered domain object
        :returns: response

        """
        epp = {
            "name": data["domain"]
        }
        if "registrant" in data:
            self.check_update_domain_registrant(data["registrant"],
                                                epp,
                                                domain,
                                                user)
        if "contacts" in data:
            self.check_update_domain_contacts(data["contacts"],
                                              epp,
                                              domain,
                                              user)
        if "ns" in data:
            self.check_update_domain_nameservers(data["ns"],
                                                 epp,
                                                 domain,
                                                 user)

        fields = ["add", "rem", "chg"]
        if len(self.workflow) > 0 or any(k in epp for k in fields):
            self.workflow.insert(0, init_update_domain.si(epp))
            self.append(update_domain.s(registry=self.registry))
            self.append(local_update_domain.s())
            return self.workflow
        log.warning("Nothing to update.")
        return None

    def process_host_addresses(self, addresses):
        """
        Preprocess address set for hosts to make compatible with
        nodepp.

        Because of Python using "type" as a reserved word, I've chosen
        to make that field "addr_type" for API requests

        :addresses: list of addresses submitted via API
        :returns: list of addresses with "addr_type" -> "type"

        """
        result = []
        for addr in addresses:
            address = {"ip": addr["ip"]}
            if "addr_type" in addr:
                address["type"] = addr["addr_type"]
            result.append(address)
        return result

    def create_host(self, data, user):
        """
        Set up workflow for creating a host

        :data: dict create host data
        :user: user object
        :returns: dict response returned by registry

        """
        self.append(check_host.s(data["host"]))
        # Need to modify outgoing data slightly
        host_data = {
            "host": data["host"],
            "addr": self.process_host_addresses(data["addr"])
        }
        self.append(create_host.si(host_data))
        self.append(connect_host.si(data, user.id))
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


class NzrsTest(Workflow):

    """
    Registry operations specific for Cocca
    """

    def __init__(self):
        super().__init__()
        self.registry = 'nzrs-test'


workflow_registries = {
    "centralnic-test": CentralNic,
    "cocca-test": CoccaTest,
    "nzrs-test": NzrsTest,
}


def workflow_factory(registry):
    """
    Return workflow manager for a given registry.


    :registry: str or DomainProvider object
    :returns: A subclass of DomainManager
    """
    return workflow_registries[registry]
