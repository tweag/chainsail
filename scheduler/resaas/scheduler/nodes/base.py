from abc import ABC, abstractmethod, abstractproperty
from concurrent.futures import Future, Executor
from enum import Enum, auto
from typing import List, Optional, Tuple
from dataclasses import dataclass

# from marshmallow import Schema, fields


class NodeType(Enum):
    LIBCLOUD_VM = "LibcloudVM"


class NodeStatus(Enum):
    INITIALIZED = auto()  # The node has been specified
    CREATING = auto()     # The node is being created and provisioned/deployed
    RUNNING = auto()      # The node is running
    RESTARTING = auto()   # The node is being restarted
    EXITED = auto()       # The node process has exited and the node is shut down
    FAILED = auto()       # The node experienced an error


# [DB] <--> {NodeModel} <--> {Scheduler} --> Node
# Scheduler lives as long as app is online
# Scheduler handles querying DB using a session
# Scheduler generates node objects using node models
# Scheduler persists node objects using node models

# NodeModel (SQLAlchemy)
# -------------------------------------
# id     type        address    status
# 1      libcloudvm  127.0.0.1  CREATED
# -------------------------------------

# Instanstiate node
# Run node.create() which creates the node and updates the status / address

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
    def db(self) -> "NodeModel":
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
