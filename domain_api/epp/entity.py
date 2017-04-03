from django_logging import log
from ..utilities.rpc_client import EppRpcClient
from application import settings


class EppEntity(object):

    """
    Represent an EPP Entity
    """

    def __init__(self, queryset=None):
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

    def process_availability_item(self,
                                  check_data,
                                  entity_type=None,):
        """
        Process check domain items.

        :check_data: item from a set of check entity results
        :returns: availability with epp attributes renamed

        """
        name_key = ":".join([entity_type, "name"])
        reason_key = ":".join([entity_type, "reason"])

        domain = check_data[name_key]['$t']
        response = {entity_type: domain, "available": False}
        available = check_data[name_key]["avail"]
        if available and int(available) == 1:
            response["available"] = True
        else:
            response["available"] = False
            if reason_key in check_data:
                response["reason"] = check_data[reason_key]
        return response
