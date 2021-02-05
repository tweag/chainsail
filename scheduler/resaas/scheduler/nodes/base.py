import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Tuple

from resaas.scheduler.db import TblJobs, TblNodes


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

    @property
    @abstractmethod
    def representation(self) -> Optional[TblNodes]:
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
    def from_representation(cls, spec, node_rep, config, is_controller=False) -> "Node":
        pass

    @classmethod
    def from_config(
        cls, name, config, spec, job_rep: Optional[TblJobs] = None, is_controller=False
    ) -> "Node":
        pass

    def sync_representation(self) -> None:
        """
        Updates the state of a node's database representation, if it exists,
        to match the state of the node.
        """
        if not self.representation:
            # If a node is created without a corresponding database row,
            # there is nothing to do
            return
        self.representation.name = self.name
        self.representation.address = self.address
        self.representation.entrypoint = self.entrypoint
        self.representation.ports = json.dumps(self.listening_ports)
        self.representation.status = self.status.value
        self.representation.node_type = self.NODE_TYPE
