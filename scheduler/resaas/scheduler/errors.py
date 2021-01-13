class BaseSchedulerException(Exception):
    """Base class for scheduler exceptions"""


class ObjectConstructionError(BaseSchedulerException):
    """
    Raised when a scheduler object cannot be loaded from its database
    representation
    """


class ConfigurationError(BaseSchedulerException):
    """Raised when there is an issue with the external config"""
