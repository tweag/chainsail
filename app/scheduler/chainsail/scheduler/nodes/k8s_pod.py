


from typing import Callable, Optional, Tuple

from chainsail.common.spec import JobSpec, JobSpecSchema
from chainsail.scheduler.config import (
    GeneralNodeConfig,
    SchedulerConfig,
    K8sNodeConfig,
    load_scheduler_config,
)
from chainsail.scheduler.db import TblJobs, TblNodes
from chainsail.scheduler.nodes.base import Node, NodeType, NodeStatus






class K8sNode(Node):
    """A resaas node implementation which creates a Kubernetes Pod for each node.
    
    """
    
    NODE_TYPE = "KubernetesPod"
    # NODE_TYPE = NodeType.KUBERNETES_POD
    
    
    def __init__(
        self,
        name: str,
        config: GeneralNodeConfig,
        representation: Optional[TblNodes] = None,
        status: Optional[NodeStatus] = None,
    ):
        self._name = name
        self._representation = representation
        self._config = config
        if not status:
            self._status = NodeStatus.INITIALIZED
        else:
            self._status = status
        # TODO address field
        self._address = None
        

    
    def create(self) -> Tuple[bool, str]:
        # TODO
        print("CREATE POD")
        return (True, "LOGS FROM CREATE...")
    
    def restart(self) -> bool:
        # TODO
        print("RESTART POD")
        return True
    
    def delete(self) -> bool:
        # TODO
        print("DELETEPOD")
        return True
    
    @property
    def name(self):
        return self._name
    
    @property
    def representation(self) -> Optional[TblNodes]:
        return self._representation
    
    @property
    def entrypoint(self):
        if self._config.args:
            args = " " + " ".join(self._config.args)
        else:
            args = ""
        return f"{self._config.cmd}{args}"
    
    @entrypoint.setter
    def entrypoint(self, value):
        self._entrypoint = value
    
    @property
    def listening_ports(self):
        return self._config.ports
    
    @property
    def address(self):
        # TODO
        return self._address

    @property
    def status(self):
        return self._status
    
    def refresh_status(self):
        # TODO
        pass
    
    @classmethod
    def from_representation(
        cls,
        spec: JobSpec,
        node_rep: TblNodes,
        scheduler_config: SchedulerConfig,
        is_controller=False,
    ) -> "Node":
        # TODO
        pass
    
    
    @classmethod
    def from_config(
        cls,
        name: str,
        scheduler_config: SchedulerConfig,
        spec: JobSpec,
        job_rep: Optional[TblJobs] = None,
        is_controller=False,
    ) -> "Node":
        
        node_config: K8sNodeConfig = scheduler_config.node_config
        if is_controller:
            config = scheduler_config.controller
        else:
            config = scheduler_config.worker
        
        
        
        
        
        
        # Bind the new node to a database record if a job record was specified
        if job_rep:
            node_rep = TblNodes(in_use=True, is_worker=(not is_controller))
            job_rep.nodes.append(node_rep)
        else:
            node_rep = None
        
        node = cls(
            name=name,
            config=config,
        )
        
        # Sync over the various fields
        node.sync_representation()
        return node
    
    

    







