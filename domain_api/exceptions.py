class EppError(Exception):

    """
    Generic EPP error.
    """
    pass


class DomainNotAvailable(Exception):
    pass


class EppObjectDoesNotExist(Exception):
    pass


class NotObjectOwner(Exception):
    pass


class UnsupportedTld(Exception):
    """
    Not a TLD we support (yet)
    """
    pass


class InvalidTld(Exception):

    """
    Invalid TLD
    """
    pass


class NoTldManager(Exception):
    pass


class UnknownContact(Exception):
    pass


class UnknownRegistry(Exception):
    pass
