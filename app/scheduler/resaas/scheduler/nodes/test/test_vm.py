from unittest.mock import Mock, patch

import pytest
from resaas.common.spec import JobSpec
from resaas.scheduler.config import GeneralNodeConfig, SchedulerConfig, VMNodeConfig
from resaas.scheduler.nodes.base import NodeType
from resaas.scheduler.nodes.mock import DeployableDummyNodeDriver


@pytest.fixture
def mock_scheduler_config():
    config = GeneralNodeConfig(
        image="foo:latest",
        cmd="bash",
        args=["-c", "'echo foo'"],
        ports=[8080],
        user_code_image="bar:earliest",
        httpstan_image="moo:sometag",
    )
    node_config = VMNodeConfig(
        "1",
        "Small",
        "ubuntu",
        "xxxxxxxxxxxxx",
        "path/to/key.pem",
        "foo/controller.yaml",
        "foo/storage.yaml",
        DeployableDummyNodeDriver,
        {"creds": "test"},
        {},
    )
    scheduler_config = SchedulerConfig(
        controller=config,
        worker=config,
        node_type=NodeType.LIBCLOUD_VM,
        node_config=node_config,
        results_url_expiry_time=42,
        remote_logging_config_path=None,
    )
    return scheduler_config


def test_vm_node_from_representation(mock_scheduler_config):
    from resaas.common.spec import JobSpec
    from resaas.scheduler.db import TblNodes
    from resaas.scheduler.nodes.base import NodeStatus, NodeType
    from resaas.scheduler.nodes.vm import VMNode

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

    node = VMNode.from_representation(job_spec, node_rep, mock_scheduler_config)
    # This method should bind node_rep to the new node
    assert node.representation


def test_vm_node_from_config_with_job(mock_scheduler_config):
    from resaas.common.spec import JobSpec
    from resaas.scheduler.db import TblJobs, TblNodes
    from resaas.scheduler.nodes.base import NodeStatus, NodeType
    from resaas.scheduler.nodes.vm import VMNode

    job_spec = JobSpec("gs://my-bucket/scripts")
    node = VMNode.from_config("dummy-1", mock_scheduler_config, job_spec, job_rep=TblJobs(id=1))
    assert node.representation
    assert node.representation.job.id == 1


def test_vm_node_from_representation_no_match_raises(mock_scheduler_config):
    from resaas.common.spec import JobSpec
    from resaas.scheduler.db import TblNodes
    from resaas.scheduler.errors import ObjectConstructionError
    from resaas.scheduler.nodes.base import NodeStatus, NodeType
    from resaas.scheduler.nodes.vm import VMNode

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
        VMNode.from_representation(job_spec, node_rep, mock_scheduler_config)


def test_vm_node_from_representation_then_create(mock_scheduler_config):
    from resaas.common.spec import JobSpec, PipDependencies
    from resaas.scheduler.db import TblJobs, TblNodes
    from resaas.scheduler.nodes.base import NodeStatus, NodeType
    from resaas.scheduler.nodes.vm import VMNode

    job_spec = JobSpec("gs://my-bucket/scripts", dependencies=[PipDependencies(["numpy"])])
    node_rep = TblNodes(
        id=1,
        job_id=1,
        name="new-node",
        node_type=NodeType.LIBCLOUD_VM,
        entrypoint="echo 'hello world'",
        # This node has not been actually created yet
        status=NodeStatus.INITIALIZED,
        job=TblJobs(),
    )

    with patch("resaas.scheduler.nodes.vm.prepare_deployment") as mock_prepare_deployment:
        # Create the node object
        node = VMNode.from_representation(
            job_spec,
            node_rep,
            mock_scheduler_config,
        )
        node.refresh_status()
        (is_created, _) = node.create()

    mock_prepare_deployment.assert_called_once()
    assert is_created
    assert node.status == NodeStatus.RUNNING


def test_vm_node_lifecycle(mock_scheduler_config):
    from resaas.scheduler.nodes.base import NodeStatus
    from resaas.scheduler.nodes.vm import VMNode

    driver = mock_scheduler_config.create_node_driver()
    job_spec = JobSpec("gs://my-bucket/scripts")

    with patch("resaas.scheduler.nodes.vm.prepare_deployment"):
        node = VMNode(
            name="test",
            driver=driver,
            size=driver.list_sizes()[0],
            image=driver.list_images()[0],
            config=mock_scheduler_config.controller,
            vm_config=mock_scheduler_config.node_config,
            spec=job_spec,
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
