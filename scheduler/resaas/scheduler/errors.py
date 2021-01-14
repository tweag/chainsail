class BaseSchedulerException(Exception):
    """Base class for scheduler exceptions"""


class ObjectConstructionError(BaseSchedulerException):
    """
    Raised when a scheduler object cannot be loaded from its database
    representation
    """


class MissingNodeError(BaseSchedulerException):
    """
    Raised when an operation is called on a node which has been
    instantiated but the corresponding compute resource has
    not been assigned yet.
    """


class ConfigurationError(BaseSchedulerException):
    """Raised when there is an issue with the external config"""
