import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Callable, Dict, List, Optional

import grpc
import shortuuid
from resaas.common.spec import JobSpec, JobSpecSchema
from resaas.grpc import HealthCheckRequest, HealthCheckResponse, HealthStub
from resaas.scheduler.config import SchedulerConfig
from resaas.scheduler.db import TblJobs, TblNodes
from resaas.scheduler.errors import JobError
from resaas.scheduler.nodes.base import Node, NodeType
from resaas.scheduler.nodes.registry import NODE_CLS_REGISTRY


class JobStatus(Enum):
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    RESTARTING = "restarting"
    STOPPING = "stopping"
    STOPPED = "stopped"
    SUCCESS = "success"
    FAILED = "failed"


N_CREATION_THREADS = 10
_DEFAULT_CONTROL_NODE = 0


# ---------------- BEGIN REXFW IMPLEMENTATION SPECIFIC STUFF ----------------
# The index of the control node. The job will use this to query for
# the health of the job node's main process.
def n_replicas_to_nodes(n_replicas: int):
    """Compute the number of nodes required to run N replicas"""
    # N replicas + 1 control node
    return n_replicas + 1


# ---------------------------------------------------------------------

# Three TODO items:
# 1. during start, the control node should be started LAST
# 2. for provisioning, some steps only need to happen on the control node
# 3. Need steps for


class Job:
    def __init__(
        self,
        id: int,
        spec: JobSpec,
        config: SchedulerConfig,
        nodes=None,
        node_registry: Dict[NodeType, Node] = NODE_CLS_REGISTRY,
        representation: Optional[TblJobs] = None,
        status: JobStatus = JobStatus.INITIALIZED,
    ):
        self.id = id
        self.spec = spec
        self.config = config
        self.driver = config.create_node_driver()
        self.representation = representation
        if nodes is None:
            self.nodes = []
        else:
            self.nodes = nodes
        self.control_node: Optional[int] = None
        self.status = status
        self._node_cls = node_registry[self.config.node_type]
        if not self.nodes:
            self._initialize_nodes()

    def _initialize_nodes(self):
        if self.nodes:
            raise JobError(
                "Cannot initialize nodes for a job which already has nodes assigned to it."
            )
        self.status = JobStatus.INITIALIZED
        self.control_node = _DEFAULT_CONTROL_NODE
        for _ in range(n_replicas_to_nodes(self.spec.initial_number_of_replicas)):
            self._add_node()
        self.sync_representation()

    def start(self) -> None:
        if self.status not in (JobStatus.INITIALIZED, JobStatus.STARTING):
            raise JobError("Attempted to start a job which has already been started")
        self.status = JobStatus.STARTING
        with ThreadPoolExecutor(max_workers=N_CREATION_THREADS) as ex:
            try:
                # Create worker nodes first
                for created, logs in ex.map(
                    lambda n: n.create(),
                    [n for i, n in enumerate(self.nodes) if i != self.control_node],
                ):
                    if not created:
                        raise JobError(
                            f"Failed to start node for job {id}. Deployment logs: \n" + logs
                        )
                self.sync_representation()
                # Then create control node
                created, logs = self.nodes[self.control_node].create()
                if not created:
                    raise JobError(
                        f"Failed to start node for job {id}. Deployment logs: \n" + logs
                    )
            except Exception as e:
                # Cleanup created nodes on failure
                for n in self.nodes:
                    n.delete()
                self.status = JobStatus.FAILED
                self.sync_representation()
                raise e
        self.status = JobStatus.RUNNING
        self.sync_representation()

    def stop(self):
        for i, node in enumerate(self.nodes):
            if not node.delete():
                self.sync_representation()
                raise JobError(f"Failed to delete node {node}")
        # Dropping references to deleted nodes
        self.nodes = []
        self.status = JobStatus.STOPPED
        self.sync_representation()

    def restart(self):
        """
        Delete all nodes and restart the job from scratch
        """
        self.stop()
        self._initialize_nodes()
        self.start()
        self.sync_representation()

    def _add_node(self) -> int:
        """Add a new node to a job"""
        if self.status in (JobStatus.STOPPED, JobStatus.SUCCESS, JobStatus.FAILED):
            raise JobError(f"Attempted to add a node to a job ({self.id}) which has exited.")
        i_new_node = len(self.nodes)
        self.nodes.append(
            self._node_cls.from_config(
                f"node-{shortuuid.uuid()}".lower(),
                self.config,
                self.spec,
                job_rep=self.representation,
                is_controller=(i_new_node == self.control_node),
            )
        )
        self.sync_representation()
        return i_new_node

    def _remove_node(self, index: int):
        """Remove a node from a job"""
        if index == self.control_node:
            raise JobError(
                "Cannot remove the control node from a job. To remove the control node use the stop() method."
            )
        node = self.nodes[index]
        if not node.delete():
            self.sync_representation()
            raise JobError(f"Failed to delete node {node} for job {self.id}")
        if node.representation:
            node.representation.in_use = False
        self.sync_representation()
        self.nodes.pop(index)

    def scale_to(self, n_replicas: int):
        if n_replicas < 0:
            raise ValueError("Can only scale to >= 0 replicas")
        if self.status != JobStatus.RUNNING:
            print(self.id)
            print(self.status)
            raise JobError(f"Attempted to scale job ({self.id}) which is not currently running.")
        requested_size = n_replicas_to_nodes(n_replicas)
        current_size = len(self.nodes)
        if requested_size == current_size:
            return None
        elif requested_size > current_size:
            # Scale up
            to_add = requested_size - current_size
            for _ in range(to_add):
                new_node = self._add_node()
                started, logs = self.nodes[new_node].create()
                if not started:
                    self.sync_representation()
                    raise JobError(f"Failed to start new node while scaling up. Logs: \n {logs}")
        else:
            # Scale down
            to_remove = current_size - requested_size
            removeable = [i for i in range(len(self.nodes)) if i != self.control_node]
            for _ in range(to_remove):
                self._remove_node(removeable.pop())
        self.sync_representation()

    def watch(self) -> bool:
        # Await control node until it reports exit or dies
        control_node: Node = self.nodes[self.control_node]
        ip = control_node.address
        port = control_node.listening_ports[0]
        with grpc.insecure_channel(f"{ip}:{port}") as channel:
            stub = HealthStub(channel)
            while True:
                response = stub.Check(HealthCheckRequest(service=""))
                if response.status != HealthCheckResponse.SERVING:
                    break
                else:
                    time.sleep(1)
        if response.status == HealthCheckResponse.SUCCESS:
            return True
        else:
            return False

    def sync_representation(self) -> None:
        """
        Updates the state of the job's database representation along with all of
        its nodes. If the Job instance is not bound to a database representation
        this method will simply return.
        """
        if not self.representation:
            return
        self.representation.status = self.status.value
        self.representation.spec = JobSpecSchema().dumps(self.spec)
        for node in self.nodes:
            node.sync_representation()

    @classmethod
    def from_representation(
        cls,
        job_rep: TblJobs,
        config: SchedulerConfig,
        node_registry: Dict[NodeType, Node] = NODE_CLS_REGISTRY,
    ) -> "Job":
        spec = JobSpecSchema().loads(job_rep.spec)
        nodes = []
        for node_rep in job_rep.nodes:
            # Ignore nodes which are no longer in use
            if not node_rep.in_use:
                continue
            node_rep: TblNodes
            node_cls = node_registry[NodeType(node_rep.node_type)]
            nodes.append(node_cls.from_representation(spec, node_rep, config))
        return cls(
            id=job_rep.id,
            spec=spec,
            config=config,
            nodes=nodes,
            node_registry=node_registry,
            representation=job_rep,
            status=JobStatus(job_rep.status),
        )
