from abc import ABC, abstractmethod, abstractproperty
from concurrent.futures import Future
from enum import Enum, auto
from typing import List

from scheduler.resaas.scheduler.jobs.restart import RestartPolicy
from scheduler.resaas.scheduler.nodes.base import Node


class JobStatus(Enum):
    INITIALIZED = auto()
    CREATING = auto()
    SUCCESS = auto()
    FAILED = auto()


# TODO: This doesn't need to be abstract
class Job(ABC):

    # Properties
    @abstractproperty
    def status(self) -> JobStatus:
        pass

    @abstractproperty
    def n_restarts(self) -> int:
        pass

    @abstractproperty
    def restart_policy(self) -> RestartPolicy:
        pass

    @abstractproperty
    def nodes(self) -> List[Node]:
        pass

    @abstractproperty
    def control_node(self) -> int:
        pass

    # Methods
    @abstractmethod
    def start(self) -> Future:
        pass

    @abstractmethod
    def stop(self) -> Future:
        pass

    @abstractmethod
    def restart(self) -> Future:
        pass

    @abstractmethod
    def add_node(self) -> Future:
        # Add another node to this job cluster
        # will need to know what specific method to use to
        # add additional nodes...
        pass

    @abstractmethod
    def watch(self):
        # TODO: Open a connection to the control node
        # using self.nodes[self.control_node]
        pass
