from ..utilities.rpc_client import EppRpcClient
from catalystinnovation import settings


class EppEntity(object):

    """
    Represent an EPP Entity
    """

    def __init__(self):
        """
        Set up rabbitmq connection.
        """
        self.rpc_client = EppRpcClient(host=settings.RABBIT_HOST)
