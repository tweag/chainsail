from abc import ABC, abstractmethod, abstractproperty
from concurrent.futures import Future, Executor
from enum import Enum, auto
from typing import List, Optional, Tuple
from dataclasses import dataclass
from resaas.scheduler.db import TblNodes


class NodeType(Enum):
    LIBCLOUD_VM = "LibcloudVM"


class NodeStatus(Enum):
    INITIALIZED = auto()  # The node has been specified
    CREATING = auto()  # The node is being created and provisioned/deployed
    RUNNING = auto()  # The node is running
    RESTARTING = auto()  # The node is being restarted
    EXITED = auto()  # The node process has exited and the node is shut down
    FAILED = auto()  # The node experienced an error


class Node(ABC):

    # Properties
    @property
    @abstractmethod
    def address(self) -> str:
        pass

    @property
    @abstractmethod
    def listening_ports(self) -> List[int]:
        pass

    @property
    @abstractmethod
    def NODE_TYPE(self) -> str:
        pass

    @property
    @abstractmethod
    def status(self) -> NodeStatus:
        pass

    @property
    @abstractmethod
    def entrypoint(self) -> str:
        pass

    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def restart(self):
        pass

    @abstractmethod
    def delete(self):
        pass

    @abstractmethod
    def refresh_status(self) -> None:
        pass

    @classmethod
    @abstractmethod
    def from_representation(cls) -> "Node":
        pass
