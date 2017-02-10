from django_logging import log
from .entity import EppEntity


class Contact(EppEntity):

    """
    Manage EPP actions for contact entities.
    """

    def __init__(self):
        """
        Create contact entity.
        """
        super().__init__()


