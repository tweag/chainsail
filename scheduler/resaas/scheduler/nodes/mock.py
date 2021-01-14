from typing import Callable, List, Optional

from libcloud.compute.base import Node as LibcloudNode
from libcloud.compute.base import T_Auth, T_Ssh_key
from libcloud.compute.deployment import Deployment
from libcloud.compute.drivers.dummy import DummyNodeDriver

from resaas.scheduler.nodes.base import Node, NodeStatus


class DeployableDummyNodeDriver(DummyNodeDriver):
    """
    A dummy driver which also implements a dummy "deploy_node()" method
    """

    def deploy_node(
        self,
        deploy,
        ssh_username="root",
        ssh_alternate_usernames=None,
        ssh_port=22,
        ssh_timeout=10,
        ssh_key=None,
        ssh_key_password=None,
        auth=None,
        timeout=30,
        max_tries=3,
        ssh_interface="public_ips",
        at_exit_func=None,
        wait_period=5,
        **create_node_kwargs,
    ) -> LibcloudNode:
        """Dummy method for "deploying" nodes. This method only calls create_node()
        and does not perform any deployment steps.
        """
        # Create the node
        return self.create_node(**create_node_kwargs)


# class MockNode(Node):
#     """
#     A simple node to use for development and integration testing. This node
#     performs all operations in memory and does not actually spin up additional
#     compute resources.
#     """

#     pass
