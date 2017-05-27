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

    @patch.object(Workflow, 'append_contact_workflow')
    @patch.object(Workflow, 'append_contact_obj_to_workflow')
    def test_create_with_custom_contacts(self, mock1, mock2):
        """
        Test that creating contacts with custom account detail object works

        """
        epp_request = {
            "contacts": [{"admin": 2}, {"tech": 1}]
        }
        workflow_class = workflow_factory('centralnic-test')
        workflow = workflow_class()
        workflow.create_contact_workflow(epp_request,
                                            self.test_customer_user)
        mock2.mock_calls == [
            call(
                {"admin": 2},
                self.test_customer_user.id),
            call(
                {"tech": 1},
                self.test_customer_user.id
        )]
        mock1.assert_not_called()
