from ..utilities.rpc_client import EppRpcClient
from application import settings


class EppEntity(object):

    """
    Represent an EPP Entity
    """

    def __init__(self):
        """
        Set up rabbitmq connection.
        """
        self.rpc_client = EppRpcClient(host=settings.RABBITMQ_HOST)
