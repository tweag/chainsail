from abc import ABC, abstractmethod, abstractproperty
from enum import Enum, auto


class Nodetatus(Enum):
    INITIALIZED = auto()
    CREATING = auto()
    SUCCESS = auto()
    FAILED = auto()


class Node(ABC):

    # Properties
    @abstractproperty
    def address(self):
        pass

    @abstractproperty
    def get_status(self):
        pass

    @abstractproperty
    def restart_policy(self):
        pass

    # Methods
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def watch(self):
        pass
