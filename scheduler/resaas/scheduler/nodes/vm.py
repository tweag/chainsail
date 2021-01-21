import json
import traceback
from typing import IO, List, Optional, Tuple, Union

from libcloud.compute.base import Node as LibcloudNode
from libcloud.compute.base import NodeAuthSSHKey, NodeDriver, NodeImage, NodeSize
from libcloud.compute.deployment import (
    Deployment,
    MultiStepDeployment,
    ScriptDeployment,
    SSHKeyDeployment,
)
from libcloud.compute.types import DeploymentException, NodeState

from resaas.scheduler.config import SchedulerConfig
from resaas.scheduler.db import TblJobs, TblNodes
from resaas.scheduler.errors import (
    ConfigurationError,
    MissingNodeError,
    NodeError,
    ObjectConstructionError,
)
from resaas.scheduler.nodes.base import Node, NodeStatus
from resaas.scheduler.spec import Dependencies, JobSpec


def _deployment_log(deployment: Deployment):
    stdout = getattr(deployment, "stdout", None)
    stderr = getattr(deployment, "stdout", None)
    log = ""
    if stdout:
        log += stdout
    if stderr:
        log += stderr
    return log


class VMNode(Node):

    NODE_TYPE = "LibcloudVM"

    # loading from db
    #   - retrieve driver using node_type
    #   - retrieve size/image using driver + node name query
    #   - create object
    #
    # k8s example:
    #   - retrieve k8s "driver" using node_type
    #   - fetch pod yaml from k8s using driver + node name

    def __init__(
        self,
        name: str,
        driver: NodeDriver,
        size: NodeSize,
        image: NodeImage,
        entrypoint: str,
        ssh_user: str,
        # Private key file for provisioning
        ssh_key_file: str,
        # Public key content
        ssh_pub: str,
        libcloud_node: Optional[LibcloudNode] = None,
        representation: Optional[TblNodes] = None,
        deps: Optional[List[Dependencies]] = None,
        listening_ports: Optional[List[int]] = None,
        status: Optional[NodeStatus] = None,
        ssh_password: Optional[str] = None,
        create_kwargs: Optional[dict] = None,
    ):
        if "create_node" not in driver.features or "ssh_key" not in driver.features["create_node"]:
            raise ValueError(
                "The supplied driver does not support node creation with ssh authentication. "
                "Please consult the libcloud documentation for a list of cloud providers which "
                f"support this method. Current driver: {driver}"
            )
        # TODO: Assert that the driver supports create_node method with "ssh_key" feature
        self._driver = driver
        self._size = size
        self._image = image
        self._node = libcloud_node
        self._ssh_user = ssh_user
        self._ssh_key_file = ssh_key_file
        self._ssh_pub = ssh_pub
        self._ssh_password = ssh_password
        self._representation = representation

        self._name = name
        self._address = None
        if listening_ports:
            self._listening_ports = listening_ports
        else:
            self._listening_ports = []
        if deps:
            self.deps = deps
        else:
            self.deps = []
        self._entrypoint = entrypoint
        if not status:
            self._status = NodeStatus.INITIALIZED
        else:
            self._status = status
        if create_kwargs is None:
            self.create_kwargs = {}
        else:
            self.create_kwargs = create_kwargs
        self.sync_representation()

    def create(self) -> Tuple[bool, str]:
        if self._status != NodeStatus.INITIALIZED:
            raise NodeError("Attempted to created a node which has already been created")
        self._status = NodeStatus.CREATING
        deployment_steps = [ScriptDeployment(dep.installation_script) for dep in self.deps] + [
            ScriptDeployment(self.entrypoint)
        ]
        try:
            self._node = self._driver.deploy_node(
                name=self.name,
                size=self._size,
                image=self._image,
                ssh_username=self._ssh_user,
                # Some common fallback options for username
                ssh_alternate_usernames=["root", "ubuntu", "resaas"],
                deploy=MultiStepDeployment(deployment_steps),
                auth=NodeAuthSSHKey(self._ssh_pub),
                ssh_key=self._ssh_key_file,
                ssh_key_password=self._ssh_password,
                wait_period=30,
                **self.create_kwargs,
            )
        except DeploymentException as e:
            self._status = NodeStatus.FAILED
            logs = (
                traceback.format_exc()
                + "\n"
                + "\n".join([_deployment_log(d) for d in deployment_steps])
            )
            if e.node:
                if not e.node.destroy():
                    # Keep node reference to enable later
                    # destroy attempts
                    self._node = e.node
            self.sync_representation()
            return (False, logs)
        else:
            logs = _deployment_log(d for d in deployment_steps)
            if self._node.private_ips:
                self._address = self._node.private_ips[0]
            self.refresh_status()
            self.sync_representation()
            return (True, logs)

    def restart(self) -> bool:
        if not self._node:
            raise MissingNodeError
        rebooted = self._node.reboot()
        self.refresh_status()
        self.sync_representation()
        return rebooted

    def delete(self) -> bool:
        if not self._node:
            return True
        deleted = self._node.destroy()
        if deleted:
            # If the delete request was successful we can go ahead
            # and flag the node as exited.
            self._status = NodeStatus.EXITED
        else:
            # Otherwise refresh the status from the driver to see
            # what the node's state is
            self.refresh_status()
        self.sync_representation()
        return deleted

    @property
    def name(self):
        return self._name

    @property
    def representation(self) -> Optional[TblNodes]:
        return self._representation

    @property
    def entrypoint(self):
        return self._entrypoint

    @entrypoint.setter
    def entrypoint(self, value):
        self._entrypoint = value

    @property
    def listening_ports(self):
        return self._listening_ports

    @property
    def address(self):
        return self._address

    @property
    def status(self):
        return self._status

    def refresh_status(self):
        # TODO: Not sure if these states are exhaustive
        if not self._node:
            self._status = NodeStatus.INITIALIZED
            return
        if self.status == NodeStatus.FAILED:
            return
        if self._node.state in (NodeState.RUNNING):
            self._status = NodeStatus.RUNNING
        elif self._node.state == NodeState.REBOOTING:
            self._status = NodeStatus.RESTARTING
        elif self._node.state in (
            NodeState.STOPPED,
            NodeState.PAUSED,
            NodeState.TERMINATED,
            NodeState.SUSPENDED,
            NodeState.STOPPING,
        ):
            self._status = NodeStatus.EXITED

        else:
            self._status = NodeStatus.FAILED

    @classmethod
    def from_representation(
        cls, spec: JobSpec, node_rep: TblNodes, config: SchedulerConfig
    ) -> "Node":

        driver: NodeDriver = config.create_node_driver()
        # If the node has only been initialized, no actual compute resource
        # has been created yet
        if node_rep.status == NodeStatus.INITIALIZED:
            node = None
            size = None  # TODO: need to look these up in config
            image = None
            name = None
        # Otherwise we can look up the compute resource using the driver
        else:
            node = [n for n in driver.list_nodes() if n.name == node_rep.name]
            if not node:
                raise ObjectConstructionError(
                    f"Failed to find an existing node with name "
                    f"{node_rep.name} job: {node_rep.job_id}, node: {node_rep.id}"
                )
            node = node[0]
            size = node.size
            image = node.image
            name = node.name
        if node_rep.ports:
            ports = json.loads(node_rep.ports)
        else:
            ports = []
        return cls(
            name=name,
            driver=driver,
            libcloud_node=node,
            size=size,
            image=image,
            deps=spec.dependencies,
            entrypoint=node_rep.entrypoint,
            listening_ports=ports,
            status=NodeStatus(node_rep.status),
            ssh_user=config.ssh_user,
            ssh_pub=config.ssh_public_key,
            ssh_key_file=config.ssh_private_key_path,
            create_kwargs=config.extra_creation_kwargs,
            representation=node_rep,
        )

    @classmethod
    def from_config(
        cls, name: str, config: SchedulerConfig, spec: JobSpec, job_rep: Optional[TblJobs] = None
    ) -> "Node":

        driver: NodeDriver = config.create_node_driver()
        # Note: constructing NodeImage directly due to performance
        # limitations of the list_images() method.
        image = NodeImage(id=config.image, name="unknown", driver=driver)
        # image = [i for i in driver.list_images() if i.name == config.image]
        size = [s for s in driver.list_sizes() if s.name == config.size]

        if not size:
            raise ConfigurationError(
                f"Failed to find node size with name '{config.size}' in driver "
                f"'{driver.__class__}'. Please update your configuration file with "
                f"a valid image name for this driver."
            )
        # Bind the new node to a database record if a job record was specified
        if job_rep:
            node_rep = TblNodes(in_use=True)
            job_rep.nodes.append(node_rep)
        else:
            node_rep = None

        node = cls(
            name=name,
            driver=driver,
            size=size[0],
            image=image,
            deps=spec.dependencies,
            entrypoint=config.node_entrypoint,
            listening_ports=config.node_ports,
            ssh_user=config.ssh_user,
            ssh_pub=config.ssh_public_key,
            ssh_key_file=config.ssh_private_key_path,
            create_kwargs=config.extra_creation_kwargs,
            representation=node_rep,
        )
        # Sync over the various fields
        node.sync_representation()
        return node
