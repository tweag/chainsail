from unittest.mock import Mock, patch
import pytest


# TODO: Can't test node creation method due to the DummyNodeDriver not supporting
# deploy_node(). Need to create our own mock for this.


def test_vm_node_from_representation():
    from libcloud.compute.drivers.dummy import DummyNodeDriver
    from resaas.scheduler.config import SchedulerConfig
    from resaas.scheduler.db import TblNodes
    from resaas.scheduler.nodes.base import NodeStatus, NodeType
    from resaas.scheduler.spec import JobSpec
    from resaas.scheduler.nodes.vm import VMNode

    # This driver already has some nodes associated with it
    driver = DummyNodeDriver("test")
    job_spec = JobSpec("gs://my-bucket/scripts")
    config = Mock(SchedulerConfig)
    config.create_node_driver.return_value = driver
    node_rep = TblNodes(
        id=1,
        job_id=1,
        name="dummy-1",
        node_type=NodeType.LIBCLOUD_VM,
        entrypoint="echo 'hello world'",
        status=NodeStatus.RUNNING,
        address="127.0.0.1",
        ports=[8080],
    )
    VMNode.from_representation(job_spec, node_rep, config)


def test_vm_node_from_representation_no_match_raises():
    from libcloud.compute.drivers.dummy import DummyNodeDriver
    from resaas.scheduler.config import SchedulerConfig
    from resaas.scheduler.db import TblNodes
    from resaas.scheduler.nodes.base import NodeStatus, NodeType
    from resaas.scheduler.spec import JobSpec
    from resaas.scheduler.nodes.vm import VMNode
    from resaas.scheduler.errors import ObjectConstructionError

    # This driver already has some nodes associated with it
    driver = DummyNodeDriver("test")
    job_spec = JobSpec("gs://my-bucket/scripts")
    config = Mock(SchedulerConfig)
    config.create_node_driver.return_value = driver
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
        VMNode.from_representation(job_spec, node_rep, config)
