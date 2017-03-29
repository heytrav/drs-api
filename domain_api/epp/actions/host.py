from django_logging import log
from ...utilities.domain import get_domain_registry
from ..entity import EppEntity


class Host(EppEntity):

    """
    Manage EPP actions for contact entities.
    """

    def __init__(self):
        """
        Create contact entity.
        """
        super().__init__()

    def create(self, host_data):
        """
        Create a host at a given registry.

        :registry: Registry to create the contact at
        :host_data: datastructure to send to EPP registry
        :returns: Result from EPP client

        """
        registry = get_domain_registry(host_data["host"])
        host_data["name"] = host_data["host"]
        result = self.rpc_client.call(registry.slug, 'createHost', host_data)

        create_data = result["host:creData"]
        log.debug(result)
        return {
            "host": create_data["host:name"],
            "create_date": create_data["host:crDate"]
        }
