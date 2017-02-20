from django_logging import log
from ..entity import EppEntity


class Domain(EppEntity):

    """
    Manage EPP actions for domain entities.
    """

    def __init__(self):
        """
        Create domain entity.
        """
        super().__init__()

    def create(self, registry, data):
        """
        Create a domain at a given registry

        :registry: Registry for domain
        :data: EPP datastructure required for domain
        :returns: Result from EPP client

        """
        log.debug(
            {
                "called": "domain_api.epp.actions.domain.create",
                "registry": registry,
                "data": data
            }
        )
        result = self.rpc_client.call(registry, 'createDomain', data)
        log.debug(result)
        create_data = result["domain:creData"]
        return {
            "create_date": create_data["domain:crDate"],
            "expiration_date": create_data["domain:exDate"]
        }
