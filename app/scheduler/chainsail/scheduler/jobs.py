import logging
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Dict, Optional
import subprocess
import tempfile

import grpc
import shortuuid
from chainsail.common.spec import JobSpec, JobSpecSchema
from chainsail.grpc import HealthCheckRequest, HealthCheckResponse, HealthStub
from chainsail.scheduler.config import SchedulerConfig
from chainsail.scheduler.db import TblJobs, TblNodes
from chainsail.scheduler.errors import JobError, ObjectConstructionError
from chainsail.scheduler.nodes.base import Node, NodeType
from chainsail.scheduler.nodes.registry import NODE_CLS_REGISTRY

JOB_CHECK_COMMAND_TEMPLATE = """
docker run \
    -e "USER_PROB_URL={prob_def}" \
    -e "USER_INSTALL_SCRIPT=/chainsail/install_job_deps.sh" \
    -e "DO_USER_CODE_CHECK=1" \
    -e "NO_SERVER=1" \
    -v {install_script_path}:/chainsail/install_job_deps.sh \
    {user_code_image}
"""


class JobStatus(Enum):
    CHECKING = "checking"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    RESTART = "restarting"
    STOPPING = "stopping"
    STOPPED = "stopped"
    SUCCESS = "success"
    FAILED = "failed"


N_CREATION_THREADS = 10

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
        status: JobStatus = JobStatus.CHECKING,
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

    def check(self) -> None:
        """
        Check that the distribution written by the user evaluates at the given initial state
        """
        if self.status != JobStatus.CHECKING:
            raise JobError("Attempted to check a job which is not to be checked")

        # Run a docker container with the user code
        # This requires a temporary file for the install script (mainly python deps atm)
        with tempfile.NamedTemporaryFile("w") as f:
            install_commands = "\n".join([d.installation_script for d in self.spec.dependencies])
            f.write(install_commands)
            f.flush()

            command = JOB_CHECK_COMMAND_TEMPLATE.format(
                prob_def=self.spec.probability_definition,
                install_script_path=f.name,
                user_code_image=self.config.controller.user_code_image,
            )
            logger.info(
                "Checking whether probability distribution for job #{self.id} can be evaluated...",
                extra={"job_id": self.id},
            )
            logger.debug("Check command : " + command)
            command_result = subprocess.run(command, shell=True, capture_output=True)
            logger.debug(
                "Check command return code: %s",
                command_result.returncode,
                extra={"job_id": self.id},
            )
            logger.info("Check command stdout:", extra={"job_id": self.id})
            for stdout_line in command_result.stdout.decode("utf-8").split("\n"):
                logger.info("  > %s", stdout_line, extra={"job_id": self.id})
            logger.info("Check command stderr:", extra={"job_id": self.id})
            for stderr_line in command_result.stderr.decode("utf-8").split("\n"):
                logger.info("  > %s", stderr_line, extra={"job_id": self.id})
            if command_result.returncode:
                raise JobError("Check command failed")

        self.status = JobStatus.INITIALIZED
        self.sync_representation()

    def _initialize_nodes(self):
        if self.status == JobStatus.CHECKING:
            raise JobError("Cannot initialize nodes for a job which is not checked yet")
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
        if self.status == JobStatus.CHECKING:
            raise JobError("Attempted to start a job which is not checked yet")
        if self.status not in (
            JobStatus.INITIALIZED,
            JobStatus.STARTING,
            JobStatus.RESTART,
        ):
            raise JobError("Attempted to start a job which has already been started")
        self._initialize_nodes()
        self.status = JobStatus.STARTING
        with ThreadPoolExecutor(max_workers=N_CREATION_THREADS) as ex:
            try:
                # Create worker nodes first
                logger.info(
                    f"Creating {len(self.nodes)} worker nodes...",
                    extra={"job_id": self.id},
                )
                for created, logs in ex.map(lambda n: n.create(), self.nodes):
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
        if n_replicas < 0:
            raise ValueError("Can only scale to >= 0 replicas")
        if self.status != JobStatus.RUNNING:
            raise JobError(f"Attempted to scale job ({self.id}) which is not currently running.")
        requested_size = n_replicas
        current_size = len(self.nodes)
        print("current / requested size", current_size, n_replicas)
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
        # TODO: this unfortunately still doesn't work.
        # Something is still off with the node representation.
        # self.control_node.listening_ports[0]
        port = 50051
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
