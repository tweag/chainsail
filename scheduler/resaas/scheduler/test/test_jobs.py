import functools
import pytest
from unittest.mock import Mock
import functools
from resaas.scheduler.nodes.mock import DeployableDummyNodeDriver
from resaas.scheduler.nodes.base import NodeStatus, NodeType


FAILURE_LOG = "deployment failed for some reason..."
SUCCESS_LOG = "deployment succeeded"
ENTRYPOINT = "bash -c 'echo foo'"


def mock_create(node: Mock, fails: bool):
    """Returns a mocked Node.create method which can be set to fail."""

    def create(node, fails):
        if fails:
            node.status = NodeStatus.FAILED
            return (False, FAILURE_LOG)
        else:
            node.status = NodeStatus.RUNNING
            return (True, SUCCESS_LOG)

    return functools.partial(create, node, fails)


def mock_restart(node: Mock, fails: bool):
    def restart(node, fails):
        if fails:
            node.status = NodeStatus.FAILED
            return False
        else:
            node.status = NodeStatus.RESTARTING
            return True

    return functools.partial(restart, node, fails)


def mock_delete(node: Mock, fails: bool):
    def delete(node, fails):
        if fails:
            node.status = NodeStatus.FAILED
            return False
        else:
            node.status = NodeStatus.EXITED
            return True

    return functools.partial(delete, node, fails)


def mk_mock_node_cls(
    create_failure: bool = False, delete_failure: bool = False, restart_failure: bool = False
):
    """
    Creates a mock Node whose various methods can be set to either succeed or fail.
    """
    node_cls = Mock("resaas.scheduler.nodes.base.Node")

    def from_config(name, config, spec):
        node = node_cls()
        node.name = name
        node.entrypoint = config.entrypoint
        node.address = "127.0.0.1"
        node.listening_ports = [8080]
        node.status = NodeStatus.INITIALIZED
        node.create = mock_create(node, create_failure)
        node.restart = mock_create(node, restart_failure)
        node.delete = mock_create(node, delete_failure)
        return node

    node_cls.from_config = from_config
    return node_cls


@pytest.fixture
def mock_config():
    config = Mock()
    config.entrypoint = ENTRYPOINT
    config.node_type = "mock"
    return config


@pytest.fixture
def mock_spec():
    spec = Mock()
    spec.initial_number_of_replicas = 5
    return spec


def test_job_init(mock_config, mock_spec):
    from resaas.scheduler.jobs import Job, JobStatus, n_replicas_to_nodes

    expected_n_nodes = n_replicas_to_nodes(mock_spec.initial_number_of_replicas)
    job = Job(id=1, spec=mock_spec, config=mock_config, node_registry={"mock": mk_mock_node_cls()})
    assert job.status == JobStatus.INITIALIZED
    assert len(job.nodes) == expected_n_nodes
    assert all([n.status == NodeStatus.INITIALIZED for n in job.nodes])


def test_job_start(mock_config, mock_spec):
    from resaas.scheduler.jobs import Job, JobStatus

    job = Job(id=1, spec=mock_spec, config=mock_config, node_registry={"mock": mk_mock_node_cls()})
    job.start()
    assert job.status == JobStatus.RUNNING
    assert all([n.status == NodeStatus.RUNNING for n in job.nodes])


def test_job_stop_running(mock_config, mock_spec):
    from resaas.scheduler.jobs import Job, JobStatus

    job = Job(id=1, spec=mock_spec, config=mock_config, node_registry={"mock": mk_mock_node_cls()})
    job.start()

    job.stop()

    assert job.status == JobStatus.STOPPED
    assert not job.nodes


def test_job_restart_running(mock_config, mock_spec):
    from resaas.scheduler.jobs import Job, JobStatus

    job = Job(id=1, spec=mock_spec, config=mock_config, node_registry={"mock": mk_mock_node_cls()})
    job.start()

    job.restart()

    assert job.status == JobStatus.RUNNING
    assert all([n.status == NodeStatus.RUNNING for n in job.nodes])


def test_job_restart_stopped(mock_config, mock_spec):
    from resaas.scheduler.jobs import Job, JobStatus

    job = Job(id=1, spec=mock_spec, config=mock_config, node_registry={"mock": mk_mock_node_cls()})
    job.start()
    job.stop()

    job.restart()

    assert job.status == JobStatus.RUNNING
    assert all([n.status == NodeStatus.RUNNING for n in job.nodes])


def test_job_scale_up(mock_config, mock_spec):
    from resaas.scheduler.jobs import Job, JobStatus

    job = Job(id=1, spec=mock_spec, config=mock_config, node_registry={"mock": mk_mock_node_cls()})
    job.start()

    job.scale_to(8)

    assert job.status == JobStatus.RUNNING
    # One extra node for the control process
    assert len(job.nodes) == 9
    assert all([n.status == NodeStatus.RUNNING for n in job.nodes])


def test_job_scale_down(mock_config, mock_spec):
    from resaas.scheduler.jobs import Job, JobStatus

    job = Job(id=1, spec=mock_spec, config=mock_config, node_registry={"mock": mk_mock_node_cls()})
    job.start()

    job.scale_to(1)

    assert job.status == JobStatus.RUNNING
    # One extra node for the control process
    assert len(job.nodes) == 2
    assert all([n.status == NodeStatus.RUNNING for n in job.nodes])


def test_scale_non_running_job_raises(mock_config, mock_spec):
    from resaas.scheduler.jobs import Job
    from resaas.scheduler.errors import JobError

    job = Job(id=1, spec=mock_spec, config=mock_config, node_registry={"mock": mk_mock_node_cls()})

    with pytest.raises(JobError):
        job.scale_to(2)


def test_vm_job_from_db_representation():
    # Note: this test uses a concrete Node implementation with a *Mock*
    # node driver.
    from resaas.scheduler.db import TblJobs, TblNodes
    from resaas.scheduler.jobs import Job
    from resaas.scheduler.nodes.base import NodeStatus
    from resaas.scheduler.jobs import JobStatus

    spec = """
    {
        "probability_definition": "gs://bucket/sub/path/script_and_data"
    }
    """
    config = Mock()
    config.entrypoint = ENTRYPOINT
    config.node_type = NodeType.LIBCLOUD_VM
    config.create_node_driver.return_value = DeployableDummyNodeDriver("test")
    job_rep = TblJobs(name="test-job", spec=spec, status=JobStatus.RUNNING)
    for i in range(2):
        job_rep.nodes.append(
            TblNodes(
                name=f"dummy-{i+1}",
                entrypoint="test",
                status=NodeStatus.RUNNING,
                node_type=NodeType.LIBCLOUD_VM,
                address=f"127.0.0.{i}",
                ports=[8080, 8081],
            )
        )

    Job.from_representation(job_rep, config)
