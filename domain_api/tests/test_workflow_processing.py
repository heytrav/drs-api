from unittest.mock import patch
from .test_setup import TestSetup
from domain_api.workflows import workflow_factory, Workflow
import domain_api
from domain_api.models import (
    RegisteredDomain
)


class MockRpcClient(domain_api.epp.entity.EppRpcClient):
    def __init__(self, host=None):
        pass


class TestUpdateWorkflow(TestSetup):

    fixtures = ["test_auth.json",
                "contact_types.json",
                "providers.json",
                "tlds.json",
                "tld_providers.json",
                "test_account_details.json",
                "default_account_contacts_non_mandatory.json",
                "test_contacts.json",
                "test_registrants.json",
                "test_domain_contacts.json",
                "test_registered_domains.json",
                "test_nameservers.json",
                ]

    def setUp(self):
        super().setUp()
        self.registered_domain = RegisteredDomain.objects.get(
            name="test-something",
            tld__zone="bar",
            active=True
        )
        self.workflow_factory = workflow_factory(
            self.registered_domain.tld_provider.provider.slug
        )()

    def test_update_domain_with_registrant_acct_template(self):
        """
        Test logic for determining if we need a new contact
        """

        possibly_new_registrant = 5  # see fixtures/test_account_details.json
        initial_workflow_count = len(self.workflow_factory.workflow)
        self.workflow_factory.check_update_domain_registrant(
            possibly_new_registrant,
            {},
            self.registered_domain,
            self.test_customer_user)

        self.assertGreater(len(self.workflow_factory.workflow),
                           initial_workflow_count,
                           "Workflow length has increased")

    def test_update_fail_domain_with_connected_registrant_acct_template(self):
        """
        Test logic for determining if we need a new contact
        """

        possibly_new_registrant = 1  # Not a new registrant
        initial_workflow_count = len(self.workflow_factory.workflow)
        self.workflow_factory.check_update_domain_registrant(
            possibly_new_registrant,
            {},
            self.registered_domain,
            self.test_customer_user)

        # Length of workflow array shouldn't change
        self.assertEqual(len(self.workflow_factory.workflow),
                         initial_workflow_count,
                         "Workflow length has increased")

    def test_update_domain_with_new_registrant(self):
        """
        Test logic for updating update command with a new registrant
        """
        possibly_new_registrant = "registrant-231"
        epp = {}
        self.workflow_factory.check_update_domain_registrant(
            possibly_new_registrant,
            epp,
            self.registered_domain,
            self.test_customer_user
        )
        self.assertIn("chg", epp, "Change structure added to epp data")
        self.assertIn("registrant", epp["chg"],
                      "Change structure added to epp data")
        self.assertEqual("registrant-231",
                         epp["chg"]["registrant"],
                         "Updating new registrant")

    def test_update_domain_fail_with_same_registrant(self):
        """
        Test logic for updating update command with the same registrant
        """
        possibly_new_registrant = "registrant-123"
        epp = {}
        self.workflow_factory.check_update_domain_registrant(
            possibly_new_registrant,
            epp,
            self.registered_domain,
            self.test_customer_user
        )
        self.assertNotIn("chg", epp, "Change structure not added to epp data")

    def test_update_domain_add_contact(self):
        """
        Test that request with new contact account detail id creates an entry
        in workflow array
        """
        # Should  result in current tech contact 4 being remove and new tech
        # contact 5 being added.
        contacts = [{"admin": 3}, {"tech": 5}]
        epp = {}
        initial_workflow_count = len(self.workflow_factory.workflow)
        self.workflow_factory.check_update_domain_contacts(
            contacts,
            epp,
            self.registered_domain,
            self.test_customer_user
        )
        self.assertGreater(
            len(self.workflow_factory.workflow),
            initial_workflow_count,
            "Workflow length has increased"
        )

    def test_update_domain_remove_contact(self):
        """
        Test that request with new contact account detail id creates an entry
        in workflow array
        """
        # Should  result in current tech contact 4 being remove and new tech
        # contact 5 being added.
        contacts = [{"admin": 3}, {"tech": 5}]
        epp = {}
        initial_workflow_count = len(self.workflow_factory.workflow)
        self.workflow_factory.check_update_domain_contacts(
            contacts,
            epp,
            self.registered_domain,
            self.test_customer_user
        )
        self.assertGreater(
            len(self.workflow_factory.workflow),
            initial_workflow_count,
            "Workflow length has increased"
        )
        self.assertIn("rem", epp, "Removing objects from domain")
        self.assertIn("contact", epp["rem"], "Removing contacts from domain")
        self.assertEqual([{"tech": "contact-321"}], epp["rem"]["contact"])

    def test_update_domain_add_contact_registry_id(self):
        """
        Test that request with new contact registry_id creates an entry
        in workflow array
        """
        # Should  result in current tech contact 4 being remove and new tech
        # contact 5 being added.
        contacts = [{"admin": 3}, {"tech": 'contact-223'}]
        epp = {}
        self.workflow_factory.check_update_domain_contacts(
            contacts,
            epp,
            self.registered_domain,
            self.user
        )
        self.assertIn("add",
                      epp,
                      "Add element has been created in update request")
        self.assertIn("contact", epp["add"], "Adding a contact")
        self.assertEqual([{"tech": "contact-223"}],
                         epp["add"]["contact"],
                         "Adding a single tech contact")

    def test_update_contacts_appended_workflow(self):
        """
        Check that workflow has been appended

        """
        epp = {
            "domain": str(self.registered_domain),
            "contacts": [{"admin": 3}, {"tech": 5}]
        }
        with patch.object(Workflow,
                          'append') as mock:
            self.workflow_factory.update_domain(
                epp,
                self.registered_domain,
                self.test_customer_user
            )
            self.assertEqual(mock.call_count,
                             3,
                             "Appended 3 orders to workflow")

    def test_update_domain_new_nameserver(self):
        """
        Test adding a new nameserver
        """
        epp = {
            "domain": str(self.registered_domain),
            "ns": ["ns1.test-08.com",
                   "ns1.test-09.com",
                   "ns2.test-10.com",
                   "ns1.newnameserver.com"]
        }
        with patch.object(Workflow,
                          'append') as mock:

            self.workflow_factory.update_domain(
                epp,
                self.registered_domain,
                self.test_customer_user
            )
            self.assertEqual(mock.call_count,
                             2,
                             "Appended 2 orders to workflow")

    def test_update_domain_new_nameserver_adds_add(self):
        """
        Test change to epp data structure when adding a new host.
        """
        ns = ["ns1.test-08.com",
              "ns1.test-09.com",
              "ns2.test-10.com",
              "ns1.newnameserver.com"]
        epp = {}
        self.workflow_factory.check_update_domain_nameservers(
            ns,
            epp,
            self.registered_domain,
            self.user
        )
        self.assertIn("add",
                      epp,
                      "Add element has been created")
        self.assertIn("ns", epp["add"], "Nameservers are being added")
        self.assertEqual(epp["add"]["ns"][0],
                         "ns1.newnameserver.com",
                         "Adding ns1.newnameserver")
        self.assertNotIn("rem", epp, "Not removing anything.")

    def test_update_domain_add_and_remove_nameserver(self):
        """
        Test change to epp data structure when adding and removing a new host.
        """
        ns = ["ns1.test-09.com",
              "ns2.test-10.com",
              "ns1.newnameserver.com"]
        epp = {}
        self.workflow_factory.check_update_domain_nameservers(
            ns,
            epp,
            self.registered_domain,
            self.user
        )
        self.assertIn("add",
                      epp,
                      "Add element has been created")
        self.assertIn("ns", epp["add"], "Nameservers are being added")
        self.assertEqual(epp["add"]["ns"][0],
                         "ns1.newnameserver.com",
                         "Adding one new nameserver")
        self.assertIn("rem", epp, "Rem element has been created")
        self.assertIn("ns", epp["rem"], "Nameservers are being removed")
        self.assertEqual(len(epp["rem"]["ns"]),
                         1,
                         "Only removing 1 element")
        self.assertEqual(epp["rem"]["ns"][0],
                         "ns1.test-08.com",
                         "ns1.test-08.com is being removed")
