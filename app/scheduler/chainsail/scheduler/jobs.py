import logging
import time
from concurrent.futures import ProcessPoolExecutor
from enum import Enum
from typing import Dict, Optional

import grpc
import shortuuid
from chainsail.common.spec import JobSpec, JobSpecSchema
from chainsail.grpc import HealthCheckRequest, HealthCheckResponse, HealthStub
from chainsail.scheduler.config import SchedulerConfig
from chainsail.scheduler.db import TblJobs, TblNodes
from chainsail.scheduler.errors import JobError, ObjectConstructionError
from chainsail.scheduler.nodes.base import Node, NodeType
from chainsail.scheduler.nodes.registry import NODE_CLS_REGISTRY


class JobStatus(Enum):
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    RESTART = "restarting"
    STOPPING = "stopping"
    STOPPED = "stopped"
    SUCCESS = "success"
    FAILED = "failed"


N_CREATION_THREADS = 3

logger = logging.getLogger("chainsail.scheduler")


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

    def _initialize_nodes(self):
        if self.nodes or self.control_node:
            raise JobError(
                "Cannot initialize nodes for a job which already has nodes assigned to it."
            )
        for _ in range(self.spec.initial_number_of_replicas):
            self._add_node()
        self.control_node = self._add_node(is_controller=True)
        self.status = JobStatus.INITIALIZED
        self.sync_representation()

    def start(self) -> None:
        if self.status not in (
            JobStatus.INITIALIZED,
            JobStatus.STARTING,
            JobStatus.RESTART,
        ):
            raise JobError("Attempted to start a job which has already been started")
        self._initialize_nodes()
        # FIXME: Parallel execution here was prone to deadlocks / serialization issues
        # need to revisit.
        # with ProcessPoolExecutor(max_workers=N_CREATION_THREADS) as ex:
        try:
            # Create worker nodes first
            logger.info(
                f"Creating {len(self.nodes)} worker nodes...",
                extra={"job_id": self.id},
            )
            for created, logs in map(lambda n: n.create(), self.nodes):
                if not created:
                    raise JobError(
                        f"Failed to start node for job {id}. Deployment logs: \n" + logs
                    )
            self.sync_representation()
            # Then create control node
            logger.debug("Creating control node...", extra={"job_id": self.id})
            logger.debug("Control node name: " + self.control_node.name)
            created, logs = self.control_node.create()
            self.sync_representation()
            if not created:
                raise JobError(f"Failed to start node for job {id}. Deployment logs: \n" + logs)
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
            logger.info(
                f"Deleting worker node {i+1}/{len(self.nodes)}...",
                extra={"job_id": self.id},
            )
            if not node.delete():
                self.sync_representation()
                raise JobError(f"Failed to delete node {node}")
        if self.control_node:
            logger.info(f"Deleting controller node...", extra={"job_id": self.id})
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
        # Indicate restart state
        self.status = JobStatus.RESTART
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
        logger.debug("Added new node", extra={"job_id": self.id})
        return new_node

    def _remove_node(self, node: Node):
        """Remove a node from a job"""
        if node == self.control_node:
            raise JobError(
                "Cannot remove the control node from a job. To remove the control node use the stop() method."
            )
        logger.debug(f"Removing node {node}...", extra={"job_id": self.id})
        if not node.delete():
            self.sync_representation()
            raise JobError(f"Failed to delete node {node} for job {self.id}")
        if node.representation:
            node.representation.in_use = False
        self.sync_representation()
        self.nodes.remove(node)

    def scale_to(self, n_replicas: int):
        logger.info("Scaling initiated")
        if n_replicas < 0:
            raise ValueError("Can only scale to >= 0 replicas")
        requested_size = n_replicas
        current_size = len(self.nodes)
        if requested_size == current_size:
            logger.info(f"Already have the requested number of replicas. Returning.")
            return None
        elif requested_size > current_size:
            logger.info(f"Scaling up from {current_size} to {n_replicas} replicas...")
            # Scale up
            to_add = requested_size - current_size
            new_nodes = [self._add_node() for _ in range(to_add)]
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=to_add) as executor:
                futures = [executor.submit(new_node.create) for new_node in new_nodes]
                for future in concurrent.futures.as_completed(futures):
                    started, logs = future.result()
                    if not started:
                        self.sync_representation()
                        raise JobError(f"Failed to start new node while scaling up. Logs: \n {logs}")
            # for _ in range(to_add):
            #     new_node = self._add_node()
            #     started, logs = new_node.create()
            #     if not started:
            #         self.sync_representation()
            #         raise JobError(f"Failed to start new node while scaling up. Logs: \n {logs}")
        else:
            # Scale down
            logger.info(f"Scaling down from {current_size} to {n_replicas} replicas...")
            to_remove = current_size - requested_size
            for node in self.nodes[-to_remove:]:
                self._remove_node(node)
        self.sync_representation()

    def watch(self) -> bool:
        # Await control node until it reports exit or dies
        ip = self.control_node.address
        # TODO: this unfortunately still doesn't work.
        # Something is still off with the node representation.
        # self.control_node.listening_ports[0]
        port = 50051
        logger.info("Initiating connection with control node")
        with grpc.insecure_channel(f"{ip}:{port}") as channel:
            stub = HealthStub(channel)
            while True:
                response = stub.Check(HealthCheckRequest(service=""))
                if response.status != HealthCheckResponse.SERVING:
                    break
                else:
                    time.sleep(1)
        logger.info("Control node connection terminated.")
        if response.status == HealthCheckResponse.SUCCESS:
            logger.info("Control node reported final status as SUCCESS")
            self.status = JobStatus.SUCCESS
            return True
        else:
            logger.info("Control node reported final status as FAILED")
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
                node = node_cls.from_representation(
                    spec, node_rep, config, is_controller=not node_rep.is_worker
                )
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
        if nodes and not control_node:
            raise JobError("Job representation had nodes but no control node.")

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
