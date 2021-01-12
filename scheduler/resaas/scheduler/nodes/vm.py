from typing import List, Optional

from libcloud.compute.deployment import MultiStepDeployment, SSHKeyDeployment, ScriptDeployment
from resaas.scheduler.spec import Dependencies
from resaas.scheduler.nodes.base import Node, NodeStatus
from libcloud.compute.base import NodeDriver, NodeImage, NodeSize
from concurrent.futures import Executor, Future
from libcloud.compute.types import DeploymentException, NodeState


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
        deps: List[Dependencies],
        entrypoint: str,
        listening_ports: Optional[List[int]] = None,
        ssh_key: Optional[str] = None,
        ssh_password: Optional[str] = None,
    ):
        self._driver = driver
        self._size = size
        self._image = image
        self._node = None
        self._ssh_key = ssh_key
        self._ssh_password = ssh_password

        self.name = name
        self._address = None
        if listening_ports:
            self._listening_ports = listening_ports
        else:
            self._listening_ports = []
        self.deps = deps
        self._entrypoint = entrypoint
        self._status = NodeStatus.INITIALIZED

    def create(self):
        if self._status != NodeStatus.INITIALIZED:
            return
        self._status = NodeStatus.CREATING
        deployment_steps = (
            [SSHKeyDeployment(self._ssh_key)]
            + [ScriptDeployment(dep.installation_script) for dep in self.deps]
            + [ScriptDeployment(self.entrypoint)]
        )
        try:
            self._node = self._driver.deploy_node(
                name=self.name,
                size=self._size,
                image=self._image,
                deploy=MultiStepDeployment(deployment_steps),
                ssh_key=self._ssh_key,
                ssh_key_password=self._ssh_password,
            )
        except DeploymentException as e:
            self._status = NodeStatus.FAILED
            for step in deployment_steps:
                # TODO: Log errors from each step
                pass
            if e.node:
                if not e.node.destroy():
                    raise Exception("Failed to destroy node")
        else:
            if self._node.private_ips:
                self._address = self._node.private_ips[0]
            self.refresh_status()

    def restart(self):
        if not self._node:
            return
        if not self._node.reboot():
            raise Exception("Could not reboot node")

    def delete(self):
        if not self._node:
            return
        else:
            if not self._node.destroy():
                raise Exception("Failed to destroy node")

    @property
    def entrypoint(self):
        return self._entrypoint

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
        if self._node.state in (NodeState.RUNNING, NodeState.STOPPING):
            self._status = NodeStatus.RUNNING
        elif self._node.state == NodeState.REBOOTING:
            self._status = NodeStatus.RESTARTING
        elif self._node.state in (
            NodeState.STOPPED,
            NodeState.PAUSED,
            NodeState.TERMINATED,
            NodeState.SUSPENDED,
        ):
            self._status = NodeStatus.EXITED

        else:
            self._status = NodeStatus.FAILED
