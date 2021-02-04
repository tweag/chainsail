import json
import traceback
from typing import IO, Callable, List, Optional, Tuple, Union

from libcloud.compute.base import Node as LibcloudNode
from libcloud.compute.base import (NodeAuthSSHKey, NodeDriver, NodeImage,
                                   NodeSize)
from libcloud.compute.deployment import (Deployment, FileDeployment,
                                         MultiStepDeployment, ScriptDeployment,
                                         SSHKeyDeployment)
from libcloud.compute.types import DeploymentException, NodeState
from resaas.common.spec import Dependencies, JobSpec
from resaas.scheduler.config import (GeneralNodeConfig, SchedulerConfig,
                                     VMNodeConfig)
from resaas.scheduler.db import TblJobs, TblNodes
from resaas.scheduler.errors import (ConfigurationError, MissingNodeError,
                                     NodeError, ObjectConstructionError)
from resaas.scheduler.nodes.base import Node, NodeStatus


def _deployment_log(deployment: Deployment):
    stdout = getattr(deployment, "stdout", None)
    stderr = getattr(deployment, "stdout", None)
    log = ""
    if stdout:
        log += stdout
    if stderr:
        log += stderr
    return log


# # https://resaas-public-data.s3.eu-central-1.amazonaws.com/test_prob_def.zip

# INSTALL_TEMPLATE = """
# #!/usr/bin/env bash

# set -ex

# # Install dependencies (if any are provided)
# {dep_install_commands}
# """


# # ssh pub
# # ssh pem
# # user_install_script

# deployment_steps = [ScriptDeployment(dep.installation_script) for dep in self.deps] + [
#     ScriptDeployment(self.entrypoint)
# ]


def get_image(driver, image_id: str) -> NodeImage:
    # Constructing the image directly since image lookups take so long on most providers
    return NodeImage(id=image_id, name="unknown", driver=driver)


def lookup_size(driver, size_name: str) -> NodeSize:
    size = [s for s in driver.list_sizes() if s.name == size_name]
    if not size:
        raise ConfigurationError(
            f"Failed to find node size with name '{size_name}' in driver "
            f"'{driver.__class__}'. Please update your configuration file with "
            f"a valid image name for this driver."
        )
    return size[0]


IPSelector = Callable[[LibcloudNode], Optional[str]]


def default_select_address(node: LibcloudNode) -> Optional[str]:
    # By default we select the first private IP
    if node.private_ips:
        return node.private_ips[0]
    else:
        return None


class VMNode(Node):

    NODE_TYPE = "LibcloudVM"

    def __init__(
        self,
        name: str,
        driver: NodeDriver,
        image: NodeImage,
        size: NodeSize,
        config: GeneralNodeConfig,
        vm_config: VMNodeConfig,
        deps: Optional[List[Dependencies]] = None,
        # If creating from an existing node, can specify the libcloud object,
        # database row, etc.
        libcloud_node: Optional[LibcloudNode] = None,
        representation: Optional[TblNodes] = None,
        status: Optional[NodeStatus] = None,
        address_selector: IPSelector = default_select_address,
    ):
        if "create_node" not in driver.features or "ssh_key" not in driver.features["create_node"]:
            raise ValueError(
                "The supplied driver does not support node creation with ssh authentication. "
                "Please consult the libcloud documentation for a list of cloud providers which "
                f"support this method. Current driver: {driver}"
            )
        self._name = name
        self._driver = driver
        self._image = image
        self._size = size
        self._config = config
        self._vm_config = vm_config
        self._node = libcloud_node
        self._address_selector = address_selector
        if self._node:
            self._address = self._address_selector(self._node)
        else:
            self._address = None
        self._representation = representation
        if deps:
            self.deps = deps
        else:
            self.deps = []
        if not status:
            self._status = NodeStatus.INITIALIZED
        else:
            self._status = status
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
                ssh_username=self._vm_config.ssh_user,
                # Some common fallback options for username
                ssh_alternate_usernames=["root", "ubuntu", "resaas"],
                deploy=MultiStepDeployment(deployment_steps),
                auth=NodeAuthSSHKey(self._vm_config.ssh_public_key),
                ssh_key=self._vm_config.ssh_private_key_path,
                wait_period=30,
                **self._vm_config.libcloud_create_node_inputs,
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
            if self._node:
                self._address = self._address_selector(self._node)
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
        cls,
        spec: JobSpec,
        node_rep: TblNodes,
        scheduler_config: SchedulerConfig,
        is_controller=False,
    ) -> "Node":

        driver: NodeDriver = scheduler_config.create_node_driver()
        node_config: VMNodeConfig = scheduler_config.node_config
        if is_controller:
            config = scheduler_config.controller
        else:
            config = scheduler_config.worker
        # If the node has only been initialized, no actual compute resource
        # has been created yet
        if node_rep.status == NodeStatus.INITIALIZED:
            node = None
            image = get_image(driver, node_config.vm_image_id)
            size = lookup_size(driver, node_config.vm_size)
            name = node_rep.name
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

        return cls(
            name=name,
            driver=driver,
            config=config,
            vm_config=node_config,
            libcloud_node=node,
            size=size,
            image=image,
            deps=spec.dependencies,
            status=NodeStatus(node_rep.status),
            representation=node_rep,
        )

    @classmethod
    def from_config(
        cls,
        name: str,
        scheduler_config: SchedulerConfig,
        spec: JobSpec,
        job_rep: Optional[TblJobs] = None,
        is_controller=False,
    ) -> "Node":

        driver: NodeDriver = scheduler_config.create_node_driver()
        vm_config: VMNodeConfig = scheduler_config.node_config
        if is_controller:
            config = scheduler_config.controller
        else:
            config = scheduler_config.worker

        # Note: constructing NodeImage directly due to performance
        # limitations of the list_images() method.
        image = get_image(driver, vm_config.vm_image_id)
        size = lookup_size(driver, vm_config.vm_size)

        # Bind the new node to a database record if a job record was specified
        if job_rep:
            node_rep = TblNodes(in_use=True)
            job_rep.nodes.append(node_rep)
        else:
            node_rep = None

        node = cls(
            name=name,
            driver=driver,
            size=size,
            config=config,
            vm_config=vm_config,
            image=image,
            deps=spec.dependencies,
            representation=node_rep,
        )
        # Sync over the various fields
        node.sync_representation()
        return node
