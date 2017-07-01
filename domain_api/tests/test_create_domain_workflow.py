from unittest.mock import patch, call
from .test_setup import TestSetup
from ..workflows import Workflow, workflow_factory
from ..models import RegisteredDomain


class TestCreateDomainNonDefaultContacts(TestSetup):

    """
    Test workflow management of create domain"""
    fixtures = ["test_auth.json", "contact_types.json",
                "providers.json",
                "tlds.json",
                "tld_providers.json",
                "test_account_details.json",
                "default_account_contacts_non_mandatory.json",
                "test_contacts.json",
                "test_registrants.json"]

    def setUp(self):
        """
        Set up test suite

        """
        super().setUp()

    @patch.object(Workflow, 'append')
    @patch.object(Workflow, 'append_contact_workflow')
    @patch.object(Workflow, 'append_contacts_to_epp')
    def test_create_with_custom_contacts(self, mock1, mock2, mock3):
        """
        Test that creating contacts with custom account detail object works

        """
        epp_request = {
            "contacts": [{"admin": 2}, {"tech": 1}]
        }
        workflow_class = workflow_factory('centralnic-test')
        workflow = workflow_class()
        epp = {}
        workflow.create_contact_workflow(epp,
                                         epp_request,
                                         self.test_customer_user)
        mock2.assert_called_with(epp,
                                 [{"admin": 2}, {"tech": 1}],
                                 self.test_customer_user.id)

    @patch.object(Workflow, 'append')
    @patch.object(Workflow, 'append_contacts_to_epp')
    def test_calls_to_append_workflow(self, mock1, mock2):
        """
        Test that creating contacts with custom account detail object works

        """
        epp_request = {
            "contacts": [{"admin": 2}, {"tech": 1}]
        }
        workflow_class = workflow_factory('centralnic-test')
        workflow = workflow_class()
        epp = {}
        workflow.create_contact_workflow(epp,
                                         epp_request,
                                         self.test_customer_user)
        self.assertEqual(2, len(mock2.mock_calls), "2 orders appended")
        mock1.assert_not_called()
