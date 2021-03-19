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
from resaas.scheduler.errors import JobError, ObjectConstructionError
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


class Job:
    def __init__(
        self,
        id: int,
        spec: JobSpec,
        config: SchedulerConfig,
        nodes=None,
        control_node=None,
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
        self.control_node = control_node
        self.status = status
        self._node_cls = node_registry[self.config.node_type]
        if not self.nodes:
            self._initialize_nodes()

    def _initialize_nodes(self):
        if self.nodes or self.control_node:
            raise JobError(
                "Cannot initialize nodes for a job which already has nodes assigned to it."
            )
        self.status = JobStatus.INITIALIZED
        for _ in range(self.spec.initial_number_of_replicas):
            self._add_node()
        self.control_node = self._add_node(is_controller=True)
        self.sync_representation()

    def start(self) -> None:
        if self.status not in (JobStatus.INITIALIZED, JobStatus.STARTING):
            raise JobError("Attempted to start a job which has already been started")
        self.status = JobStatus.STARTING
        with ThreadPoolExecutor(max_workers=N_CREATION_THREADS) as ex:
            try:
                # Create worker nodes first
                for created, logs in ex.map(lambda n: n.create(), self.nodes):
                    if not created:
                        raise JobError(
                            f"Failed to start node for job {id}. Deployment logs: \n" + logs
                        )
                # Then create control node
                created, logs = self.control_node.create()
                if not created:
                    raise JobError(
                        f"Failed to start node for job {id}. Deployment logs: \n" + logs
                    )
                self.sync_representation()
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
        for node in self.nodes:
            if not node.delete():
                self.sync_representation()
                raise JobError(f"Failed to delete node {node}")
        if self.control_node:
            if not self.control_node.delete():
                self.sync_representation()
                raise JobError(f"Failed to delete node {node}")
        # Dropping references to deleted nodes
        self.nodes = []
        self.control_node = None
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

    def _add_node(self, is_controller=False) -> Node:
        """Add a new node to a job"""
        if self.status in (JobStatus.STOPPED, JobStatus.SUCCESS, JobStatus.FAILED):
            raise JobError(f"Attempted to add a node to a job ({self.id}) which has exited.")
        new_node = self._node_cls.from_config(
            f"node-{shortuuid.uuid()}".lower(),
            self.config,
            self.spec,
            job_rep=self.representation,
            is_controller=is_controller,
        )
        if not is_controller:
            self.nodes.append(new_node)
        else:
            if self.control_node:
                raise JobError(
                    f"Attempted to add a controller node to job ({self.id}) which already has one."
                )
            self.control_node = new_node
        self.sync_representation()
        return new_node

    def _remove_node(self, node: Node):
        """Remove a node from a job"""
        if node == self.control_node:
            raise JobError(
                "Cannot remove the control node from a job. To remove the control node use the stop() method."
            )
        if not node.delete():
            self.sync_representation()
            raise JobError(f"Failed to delete node {node} for job {self.id}")
        if node.representation:
            node.representation.in_use = False
        self.sync_representation()
        self.nodes.remove(node)

    def scale_to(self, n_replicas: int):
        if n_replicas < 0:
            raise ValueError("Can only scale to >= 0 replicas")
        if self.status != JobStatus.RUNNING:
            print(self.id)
            print(self.status)
            raise JobError(f"Attempted to scale job ({self.id}) which is not currently running.")
        requested_size = n_replicas
        current_size = len(self.nodes)
        if requested_size == current_size:
            return None
        elif requested_size > current_size:
            # Scale up
            to_add = requested_size - current_size
            for _ in range(to_add):
                new_node = self._add_node()
                started, logs = new_node.create()
                if not started:
                    self.sync_representation()
                    raise JobError(f"Failed to start new node while scaling up. Logs: \n {logs}")
        else:
            # Scale down
            to_remove = current_size - requested_size
            for node in self.nodes[-to_remove:]:
                self._remove_node(node)
        self.sync_representation()

    def watch(self) -> bool:
        # Await control node until it reports exit or dies
        ip = self.control_node.address
        port = self.control_node.listening_ports[0]
        with grpc.insecure_channel(f"{ip}:{port}") as channel:
            stub = HealthStub(channel)
            while True:
                response = stub.Check(HealthCheckRequest(service=""))
                if response.status != HealthCheckResponse.SERVING:
                    break
                else:
                    time.sleep(1)
        if response.status == HealthCheckResponse.SUCCESS:
            self.status = JobStatus.SUCCESS
            return True
        else:
            self.status = JobStatus.FAILED
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
        if self.control_node:
            self.control_node.sync_representation()

    @classmethod
    def from_representation(
        cls,
        job_rep: TblJobs,
        config: SchedulerConfig,
        node_registry: Dict[NodeType, Node] = NODE_CLS_REGISTRY,
    ) -> "Job":
        spec = JobSpecSchema().loads(job_rep.spec)
        nodes = []
        control_node = None
        for node_rep in job_rep.nodes:
            # Ignore nodes which are no longer in use
            if not node_rep.in_use:
                continue
            node_rep: TblNodes
            node_cls = node_registry[NodeType(node_rep.node_type)]
            try:
                node = node_cls.from_representation(spec, node_rep, config)
            except ObjectConstructionError:
                node_rep.in_use = False
            else:
                if node_rep.is_worker:
                    nodes.append(node)
                else:
                    if not control_node:
                        control_node = node
                    else:
                        raise JobError("Job representation has more than one control node.")
        if not control_node:
            JobError("Job representation has no control node.")

        return cls(
            id=job_rep.id,
            spec=spec,
            config=config,
            nodes=nodes,
            control_node=control_node,
            node_registry=node_registry,
            representation=job_rep,
            status=JobStatus(job_rep.status),
        )
