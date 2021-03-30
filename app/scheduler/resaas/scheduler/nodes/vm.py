import logging
import os
import traceback
from tempfile import TemporaryDirectory
from typing import Callable, Optional, Tuple

from libcloud.compute.base import Node as LibcloudNode
from libcloud.compute.base import NodeDriver, NodeImage, NodeSize
from libcloud.compute.deployment import (
    Deployment,
    FileDeployment,
    MultiStepDeployment,
    ScriptDeployment,
    SSHKeyDeployment,
)
from libcloud.compute.types import DeploymentException, NodeState
from resaas.common.spec import JobSpec, JobSpecSchema
from resaas.scheduler.config import (
    GeneralNodeConfig,
    SchedulerConfig,
    VMNodeConfig,
    load_scheduler_config,
)
from resaas.scheduler.db import TblJobs, TblNodes
from resaas.scheduler.errors import (
    ConfigurationError,
    MissingNodeError,
    NodeError,
    ObjectConstructionError,
)
from resaas.scheduler.nodes.base import Node, NodeStatus


logger = logging.getLogger("resaas.scheduler")


def _raise_for_exit_status(node: LibcloudNode, deployment: Deployment):
    if hasattr(deployment, "exit_status"):
        status = deployment.exit_status
        if status != 0:
            raise DeploymentException(node)


def _deployment_log(deployment: Deployment):
    stdout = getattr(deployment, "stdout", None)
    stderr = getattr(deployment, "stderr", None)
    log = ""
    if stdout:
        log += stdout
    if stderr:
        log += stderr
    return log


DEP_INSTALL_TEMPLATE = """#!/usr/bin/env bash

set -ex

# Install dependencies (if any are provided)
{dep_install_commands}
"""

COMMAND_TEMPLATE = """#!/usr/bin/env bash

set -ex

docker run -d \
    -e "USER_PROB_URL={prob_def}" \
    -e "USER_INSTALL_SCRIPT=/resaas/{install_script}" \
    -e "USER_CODE_SERVER_PORT=50052" \
    -v {config_dir}:/resaas \
    --network host \
    -p 50052 \
    --log-driver=gcplogs \
    {user_code_image} {user_code_cmd}

docker run -d \
    --network host \
    -v {config_dir}:/resaas \
    -v {authorized_keys}:/app/config/ssh/authorized_keys \
    -v {pem_file}:/root/.ssh/id.pem \
    -p 50051 \
    --log-driver=gcplogs \
    {image} {cmd}
"""

MK_TARGET_TEMPLATE = """#!/usr/bin/env bash
set -ex

mkdir -p $HOME/.ssh
mkdir -p '{target_dir}'

"""

DeploymentPreparer = Callable[..., MultiStepDeployment]


def prepare_deployment(
    vm_node: "VMNode", staging_dir: str, install_dir: str = ""
) -> MultiStepDeployment:
    """Prepares deployment steps, writing intermediate files to staging_dir

    Args:
        staging_dir: Path to a temporary staging directory in which to write generated files for
            `FileDeployment` steps.
        install_dir: Path on remote host in which to install configuration files. You should only
            pass **absolute paths** here since libcloud's ssh client has undefined behavior for
            MultiStepDeployments which rely on relative paths.

    Returns:
        The combined deployment steps
    """
    # Prepare installer script
    install_commands = "\n".join([d.installation_script for d in vm_node.spec.dependencies])
    install_script_name = "install_job_deps.sh"
    install_script_src = os.path.join(staging_dir, install_script_name)
    install_script_target = os.path.join(install_dir, install_script_name)
    with open(install_script_src, "w") as f:
        f.write(DEP_INSTALL_TEMPLATE.format(dep_install_commands=install_commands))

    # Prepare initial hostfile with known peers
    hosts = []
    if vm_node._representation:
        # Note: assuming that we are already within a session context
        job: TblJobs = vm_node._representation.job
        for node in job.nodes:
            node: TblNodes
            # Note: nodes at this stage don't generally have a database ID
            #   so we compare on name.
            if node.name == vm_node._representation.name:
                continue
            if node.in_use and node.address:
                print("Adding node to hostfile")
                hosts.append(node.address)
    hostfile_name = "hostfile"
    hostfile_src = os.path.join(staging_dir, hostfile_name)
    hostfile_target = os.path.join(install_dir, hostfile_name)
    with open(hostfile_src, "w") as f:
        for h in hosts:
            print(h, file=f)

    # Serialize job spec to copy it to the various nodes
    spec_file_name = "job.json"
    spec_file_src = os.path.join(staging_dir, spec_file_name)
    spec_file_target = os.path.join(install_dir, spec_file_name)
    with open(spec_file_src, "w") as f:
        f.write(JobSpecSchema().dumps(vm_node.spec))

    # Private key path
    ssh_private_key_src = vm_node._vm_config.ssh_private_key_path
    ssh_private_key_target = os.path.join(install_dir, os.path.basename(ssh_private_key_src))

    # Final command to start up the main process
    # Format the command + args into a single string
    container_cmd = vm_node._config.cmd
    if vm_node._config.args:
        # Extra leading whitespace
        container_cmd += " "
        container_cmd += " ".join([a for a in vm_node._config.args])

    container_cmd = container_cmd.format(job_id=vm_node.representation.job.id)
    user_code_cmd = "python /app/app/user_code_server/resaas/user_code_server/__init__.py"
    command = COMMAND_TEMPLATE.format(
        prob_def=vm_node.spec.probability_definition,
        install_script=os.path.basename(install_script_target),
        config_dir=install_dir,
        # This is where libcloud installs public keys to
        authorized_keys="$HOME/.ssh/authorized_keys",
        pem_file=ssh_private_key_target,
        image=vm_node._config.image,
        cmd=container_cmd,
        user_code_image=vm_node._config.user_code_image,
        user_code_cmd=user_code_cmd,
    )

    scheduler_config = load_scheduler_config()
    steps = MultiStepDeployment(
        [
            # The very first thing to do is run the initialization script to ensure
            # that credential helpers, etc. are initialized.
            ScriptDeployment(vm_node._vm_config.init_script),
            # Prepare config directory
            ScriptDeployment(MK_TARGET_TEMPLATE.format(target_dir=install_dir)),
            # public ssh key for openmpi and general use
            SSHKeyDeployment(vm_node._vm_config.ssh_public_key),
            # Installer script
            FileDeployment(
                install_script_src,
                install_script_target,
            ),
            # Hostfile
            FileDeployment(
                hostfile_src,
                hostfile_target,
            ),
            # Job spec
            FileDeployment(
                spec_file_src,
                spec_file_target,
            ),
            # Storage backend config
            FileDeployment(
                vm_node._vm_config.storage_config_path,
                os.path.join(
                    install_dir,
                    os.path.basename(vm_node._vm_config.storage_config_path),
                ),
            ),
            # Controller config
            FileDeployment(
                vm_node._vm_config.controller_config_path,
                os.path.join(
                    install_dir,
                    os.path.basename(vm_node._vm_config.controller_config_path),
                ),
            ),
            # Remote logging config
            FileDeployment(
                scheduler_config.remote_logging_config_path,
                os.path.join(
                    install_dir,
                    os.path.basename(scheduler_config.remote_logging_config_path),
                ),
            ),
            # private ssh key for openmpi to use
            FileDeployment(
                ssh_private_key_src,
                ssh_private_key_target,
            ),
            # Start the main process. This is expected to return immediately after the process starts
            ScriptDeployment(command),
        ]
    )

    return steps


# TODO: Add caching here
def get_image(driver, image_id: str) -> NodeImage:
    # Constructing the image directly since image lookups take so long on most providers
    # return NodeImage(id=image_id, name="unknown", driver=driver)
    img = None
    for i in driver.list_images():
        if i.id == image_id:
            img = i
            break
    if not img:
        raise ConfigurationError(
            f"Failed to find node image with id '{image_id}' in driver "
            f"'{driver.__class__}'. Please update your configuration file with "
            f"a valid image name for this driver."
        )
    return img


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
    """A resaas node implementation which creates a VM for each node using libcloud.

    Requires that docker is installed in the provided `image`

    """

    NODE_TYPE = "LibcloudVM"

    def __init__(
        self,
        name: str,
        driver: NodeDriver,
        image: NodeImage,
        size: NodeSize,
        config: GeneralNodeConfig,
        vm_config: VMNodeConfig,
        spec: JobSpec,
        # If creating from an existing node, can specify the libcloud object,
        # database row, etc.
        libcloud_node: Optional[LibcloudNode] = None,
        representation: Optional[TblNodes] = None,
        status: Optional[NodeStatus] = None,
        address_selector: Optional[IPSelector] = None,
        deployment: Optional[DeploymentPreparer] = None,
    ):
        if "create_node" not in driver.features or "ssh_key" not in driver.features["create_node"]:
            raise ValueError(
                "The supplied driver does not support node creation with ssh authentication. "
                "Please consult the libcloud documentation for a list of cloud providers which "
                f"support this method. Current driver: {driver}"
            )
        # TODO: Make the representation a mandatory field and check that it has a valid job id associated with it
        self._name = name
        self._driver = driver
        self._image = image
        self._size = size
        self._config = config
        self._vm_config = vm_config
        self._node = libcloud_node
        if not address_selector:
            self._address_selector = default_select_address
        else:
            self._address_selector = address_selector
        if not deployment:
            self._deployment = prepare_deployment
        else:
            self._deployment = deployment
        if self._node:
            self._address = self._address_selector(self._node)
        else:
            self._address = None
        self._representation = representation
        self.spec = spec
        if not status:
            self._status = NodeStatus.INITIALIZED
        else:
            self._status = status
        self.sync_representation()

    def create(self) -> Tuple[bool, str]:
        if self._status != NodeStatus.INITIALIZED:
            raise NodeError("Attempted to created a node which has already been created")
        logger.info("Creating node...")
        self._status = NodeStatus.CREATING
        with TemporaryDirectory() as tmpdir:
            deployment_steps = self._deployment(
                self, tmpdir, install_dir=f"/home/{self._vm_config.ssh_user}/resaas"
            )
            for s in deployment_steps.steps:
                print(s)
            try:
                self._node = self._driver.deploy_node(
                    name=self.name,
                    size=self._size,
                    image=self._image,
                    ssh_username=self._vm_config.ssh_user,
                    # Some common fallback options for username
                    ssh_alternate_usernames=["root", "ubuntu", "resaas"],
                    deploy=deployment_steps,
                    # auth=NodeAuthSSHKey(self._vm_config.ssh_public_key),
                    ssh_key=self._vm_config.ssh_private_key_path,
                    wait_period=10,
                    **self._vm_config.libcloud_create_node_inputs,
                )
                for s in deployment_steps.steps:
                    # Ensure that scripts all exited successfully
                    _raise_for_exit_status(self._node, s)

            except DeploymentException as e:
                self._status = NodeStatus.FAILED
                logs = (
                    traceback.format_exc()
                    + "\n"
                    + "\n".join([_deployment_log(d) for d in deployment_steps.steps])
                )
                if e.node:
                    if not e.node.destroy():
                        # Keep node reference to enable later
                        # destroy attempts
                        self._node = e.node
                    else:
                        self._node = None
                self.sync_representation()
                return (False, logs)
            else:
                logs = _deployment_log(d for d in deployment_steps.steps)
                if self._node:
                    self._address = self._address_selector(self._node)
                self.refresh_status()
                self.sync_representation()
                return (True, logs)

    def restart(self) -> bool:
        if not self._node:
            raise MissingNodeError
        logger.info("Restarting node...")
        rebooted = self._node.reboot()
        self.refresh_status()
        self.sync_representation()
        return rebooted

    def delete(self) -> bool:
        if not self._node:
            return True
        logger.info("Deleting node...")
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
            spec=spec,
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
            node_rep = TblNodes(in_use=True, is_worker=(not is_controller))
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
            spec=spec,
            representation=node_rep,
        )
        # Sync over the various fields
        node.sync_representation()
        return node
