from unittest.mock import Mock

import pytest

from resaas.scheduler.config import SchedulerConfig
from resaas.scheduler.nodes.mock import DeployableDummyNodeDriver


@pytest.fixture
def mock_config():
    driver = DeployableDummyNodeDriver("test")
    config = Mock(SchedulerConfig)
    config.ssh_user = "user"
    config.ssh_public_key = "testing"
    config.ssh_private_key_path = "./foo/bar"
    config.node_entrypoint = "bash -c 'echo foo'"
    config.image = "Ubuntu 9.10"
    config.node_ports = "[8080]"
    config.size = "Small"
    config.node_type = "LibcloudVM"
    config.create_node_driver.return_value = driver
    config.extra_creation_kwargs = {}
    return config


def test_vm_node_from_representation(mock_config):
    from resaas.scheduler.db import TblNodes
    from resaas.scheduler.nodes.base import NodeStatus, NodeType
    from resaas.scheduler.nodes.vm import VMNode
    from resaas.scheduler.spec import JobSpec

    job_spec = JobSpec("gs://my-bucket/scripts")
    node_rep = TblNodes(
        id=1,
        job_id=1,
        # dummy-1 already exists on the driver
        name="dummy-1",
        node_type=NodeType.LIBCLOUD_VM,
        entrypoint="echo 'hello world'",
        status=NodeStatus.RUNNING,
        address="127.0.0.1",
        ports="[8080]",
    )

    node = VMNode.from_representation(job_spec, node_rep, mock_config)
    # This method should bind node_rep to the new node
    assert node.representation


def test_vm_node_from_config_with_job(mock_config):
    from resaas.scheduler.db import TblJobs, TblNodes
    from resaas.scheduler.nodes.base import NodeStatus, NodeType
    from resaas.scheduler.nodes.vm import VMNode
    from resaas.scheduler.spec import JobSpec

    job_spec = JobSpec("gs://my-bucket/scripts")
    node = VMNode.from_config("dummy-1", mock_config, job_spec, job_rep=TblJobs(id=1))
    assert node.representation
    assert node.representation.job.id == 1


def test_vm_node_from_representation_no_match_raises(mock_config):
    from resaas.scheduler.db import TblNodes
    from resaas.scheduler.errors import ObjectConstructionError
    from resaas.scheduler.nodes.base import NodeStatus, NodeType
    from resaas.scheduler.nodes.vm import VMNode
    from resaas.scheduler.spec import JobSpec

    job_spec = JobSpec("gs://my-bucket/scripts")
    node_rep = TblNodes(
        id=1,
        job_id=1,
        name="does not exist in driver",
        node_type=NodeType.LIBCLOUD_VM,
        entrypoint="echo 'hello world'",
        status=NodeStatus.RUNNING,
        address="127.0.0.1",
        ports=[8080],
    )

    with pytest.raises(ObjectConstructionError):
        VMNode.from_representation(job_spec, node_rep, mock_config)


def test_vm_node_from_representation_then_create(mock_config):
    from resaas.scheduler.db import TblNodes
    from resaas.scheduler.nodes.base import NodeStatus, NodeType
    from resaas.scheduler.nodes.vm import VMNode
    from resaas.scheduler.spec import JobSpec, PipDependencies

    job_spec = JobSpec("gs://my-bucket/scripts", dependencies=[PipDependencies(["numpy"])])
    node_rep = TblNodes(
        id=1,
        job_id=1,
        name="new-node",
        node_type=NodeType.LIBCLOUD_VM,
        entrypoint="echo 'hello world'",
        # This node has not been actually created yet
        status=NodeStatus.INITIALIZED,
    )

    # Create the node object
    node = VMNode.from_representation(job_spec, node_rep, mock_config)
    node.refresh_status()

    assert node.create()
    assert node.status == NodeStatus.RUNNING


def test_vm_node_lifecycle(mock_config):
    from resaas.scheduler.nodes.base import NodeStatus
    from resaas.scheduler.nodes.vm import VMNode

    driver = mock_config.create_node_driver()
    node = VMNode(
        name="test",
        driver=mock_config.create_node_driver(),
        size=driver.list_sizes()[0],
        image=driver.list_images()[0],
        entrypoint="echo 'foo'",
        ssh_user=mock_config.ssh_user,
        ssh_pub=mock_config.ssh_public_key,
        ssh_key_file=mock_config.ssh_private_key_path,
    )

    statuses = [node.status]
    is_created, _ = node.create()
    statuses.append(node.status)
    is_restarted = node.restart()
    statuses.append(node.status)
    is_deleted = node.delete()
    statuses.append(node.status)

    # Check that all operations succeeded
    assert all([is_created, is_restarted, is_deleted])
    # If so, the following statuses should have been observed:
    assert statuses == [
        NodeStatus.INITIALIZED,
        NodeStatus.RUNNING,
        NodeStatus.RESTARTING,
        NodeStatus.EXITED,
    ]
