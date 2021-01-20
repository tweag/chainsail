from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Tuple


class NodeType(Enum):
    LIBCLOUD_VM = "LibcloudVM"


class NodeStatus(Enum):
    INITIALIZED = "initialized"  # The node has been specified
    CREATING = "creating"  # The node is being created and provisioned/deployed
    RUNNING = "running"  # The node is running
    RESTARTING = "restarting"  # The node is being restarted
    EXITED = "exited"  # The node process has exited and the node is shut down
    FAILED = "failed"  # The node experienced an error


class Node(ABC):

    # Properties
    @property
    @abstractmethod
    def address(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
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
    def create(self) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def restart(self) -> bool:
        pass

    @abstractmethod
    def delete(self) -> bool:
        pass

    @abstractmethod
    def refresh_status(self) -> None:
        pass

    @classmethod
    @abstractmethod
    def from_representation(cls, spec, node_rep, config) -> "Node":
        pass

    @classmethod
    def from_config(cls, name, config, spec) -> "Node":
        pass
