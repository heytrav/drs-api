import logging
from ..entity import EppEntity

log = logging.getLogger(__name__)

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
        log.debug("Create a domain at %s" % registry)
        result = self.rpc_client.call(registry, 'createDomain', data)
        log.debug("{!r}".format(result))
        create_data = result["domain:creData"]
        return {
            "create_date": create_data["domain:crDate"],
            "expiration_date": create_data["domain:exDate"]
        }
