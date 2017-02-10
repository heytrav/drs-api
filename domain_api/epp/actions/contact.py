from django_logging import log
from ..entity import EppEntity


class Contact(EppEntity):

    """
    Manage EPP actions for contact entities.
    """

    def __init__(self):
        """
        Create contact entity.
        """
        super().__init__()


    def create(self, registry, contact_data):
        """
        Create a contact at a given registry.

        :registry: Registry to create the contact at
        :contact_data: datastructure to send to EPP registry
        :returns: Result from EPP client

        """
        result = self.rpc_client.call(registry, 'createContact', contact_data)

        create_data = result["contact:creData"]
        return {
            "id": create_data["contact:id"],
            "create_date": create_data["contact:crDate"]
        }
