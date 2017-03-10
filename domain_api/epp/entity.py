from ..utilities.rpc_client import EppRpcClient
from application import settings


class EppEntity(object):

    """
    Represent an EPP Entity
    """

    def __init__(self, queryset):
        """
        Set up rabbitmq connection.
        """
        self.queryset = queryset
        self.rpc_client = EppRpcClient(host=settings.RABBITMQ_HOST)

    def process_status(self, raw_status):
        """
        Process the entity status returned by infoDomain/infoContact

        :raw_status: dict containing EPP status
        :returns: status info processed into set

        """
        return_status = []
        try:
            if isinstance(raw_status, dict):
                return_status.append(raw_status["s"])
            elif isinstance(raw_status, list):
                for stat in raw_status:
                    return_status.append(stat["s"])
            return ";".join(return_status)
        except Exception as e:
            log.error({"msg": "Problem parsing status", "error": e})
