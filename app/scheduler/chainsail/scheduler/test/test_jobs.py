import functools
from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest
from chainsail.common.spec import JobSpec, JobSpecSchema
from chainsail.scheduler.config import GeneralNodeConfig, SchedulerConfig, VMNodeConfig
from chainsail.scheduler.errors import JobError
from chainsail.scheduler.nodes.base import NodeStatus, NodeType
from chainsail.scheduler.nodes.mock import DeployableDummyNodeDriver

FAILURE_LOG = "deployment failed for some reason..."
SUCCESS_LOG = "deployment succeeded"


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
    create_failure: bool = False,
    delete_failure: bool = False,
    restart_failure: bool = False,
):
    """
    Creates a mock Node whose various methods can be set to either succeed or fail.
    """
    from chainsail.scheduler.nodes.base import Node

    # https://stackoverflow.com/a/59019431/1656472
    class NodeClassMeta(type):
        static_instance = MagicMock(spec="chainsail.scheduler.nodes.base.Node")

        def __getattr__(cls, key):
            return NodeClassMeta.static_instance.__getattr__(key)

    class NodeClass(metaclass=NodeClassMeta):
        original_cls = Node
        instances = []

        def __new__(cls, *args, **kwargs):
            NodeClass.instances.append(MagicMock(spec=NodeClass.original_cls))
            NodeClass.instances[-1].__class__ = NodeClass
            return NodeClass.instances[-1]

    node_cls = NodeClass

    def from_config(
        name,
        config,
        spec,
        is_controller,
        job_rep=None,
    ):
        node = node_cls()
        node.name = name
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
    config = SchedulerConfig(
        controller=GeneralNodeConfig(
            image="foo:latest",
            cmd="echo",
            args=["bar"],
            ports=[8080],
            user_code_image="bar:earliest",
            httpstan_image="moo:laitest (funny for French speaking people)",
        ),
        worker=GeneralNodeConfig(
            image="foo:latest",
            cmd="echo",
            args=["bar"],
            ports=[8080],
            user_code_image="bar:earliest",
            httpstan_image="moo:laitest (funny for French speaking people)",
        ),
        node_type="mock",
        node_config=VMNodeConfig(
            "Ubuntu 9.10",
            "Small",
            "ubuntu",
            "xxxxxxxxxxxxx",
            "path/to/key.pem",
            "foo/controller.yaml",
            "foo/storage.yaml",
            DeployableDummyNodeDriver,
            {"creds": "test"},
            {},
        ),
        results_url_expiry_time=42,
        remote_logging_config_path=None,
    )
    return config


@pytest.fixture
def mock_spec():
    spec = Mock()
    spec.initial_number_of_replicas = 5
    return spec


def test_job_init(mock_config, mock_spec):
    from chainsail.scheduler.jobs import Job, JobStatus

    job = Job(
        id=1,
        spec=mock_spec,
        config=mock_config,
        node_registry={"mock": mk_mock_node_cls()},
    )
    assert job.status == JobStatus.CHECKING
    assert not job.nodes


def test_job_start_unchecked(mock_config, mock_spec):
    from chainsail.scheduler.jobs import Job, JobStatus

    job = Job(
        id=1,
        spec=mock_spec,
        config=mock_config,
        node_registry={"mock": mk_mock_node_cls()},
        status=JobStatus.CHECKING,
    )
    with pytest.raises(JobError):
        job.start()

    assert job.status == JobStatus.CHECKING


def test_job_start_checked(mock_config, mock_spec):
    from chainsail.scheduler.jobs import Job, JobStatus

    job = Job(
        id=1,
        spec=mock_spec,
        config=mock_config,
        node_registry={"mock": mk_mock_node_cls()},
        status=JobStatus.INITIALIZED,
    )
    job.start()
    assert job.status == JobStatus.RUNNING
    assert all([n.status == NodeStatus.RUNNING for n in job.nodes])


def test_job_stop_running(mock_config, mock_spec):
    from chainsail.scheduler.jobs import Job, JobStatus

    job = Job(
        id=1,
        spec=mock_spec,
        config=mock_config,
        node_registry={"mock": mk_mock_node_cls()},
        status=JobStatus.INITIALIZED,
    )
    job.start()

    job.stop()

    assert job.status == JobStatus.STOPPED
    assert not job.nodes


def test_job_restart_running(mock_config, mock_spec):
    from chainsail.scheduler.jobs import Job, JobStatus

    job = Job(
        id=1,
        spec=mock_spec,
        config=mock_config,
        node_registry={"mock": mk_mock_node_cls()},
        status=JobStatus.INITIALIZED,
    )
    job.start()

    job.restart()

    assert job.status == JobStatus.RUNNING
    assert all([n.status == NodeStatus.RUNNING for n in job.nodes])


def test_job_restart_stopped(mock_config, mock_spec):
    from chainsail.scheduler.jobs import Job, JobStatus

    job = Job(
        id=1,
        spec=mock_spec,
        config=mock_config,
        node_registry={"mock": mk_mock_node_cls()},
        status=JobStatus.INITIALIZED,
    )
    job.start()
    job.stop()

    job.restart()

    assert job.status == JobStatus.RUNNING
    assert all([n.status == NodeStatus.RUNNING for n in job.nodes])


def test_job_scale_up(mock_config, mock_spec):
    from chainsail.scheduler.jobs import Job, JobStatus

    job = Job(
        id=1,
        spec=mock_spec,
        config=mock_config,
        node_registry={"mock": mk_mock_node_cls()},
        status=JobStatus.INITIALIZED,
    )
    job.start()
    job.scale_to(8)

    assert job.status == JobStatus.RUNNING
    assert len(job.nodes) == 8
    assert all([n.status == NodeStatus.RUNNING for n in job.nodes])


def test_job_scale_down(mock_config, mock_spec):
    from chainsail.scheduler.jobs import Job, JobStatus

    job = Job(
        id=1,
        spec=mock_spec,
        config=mock_config,
        node_registry={"mock": mk_mock_node_cls()},
        status=JobStatus.INITIALIZED,
    )
    job.start()

    job.scale_to(1)

    assert job.status == JobStatus.RUNNING
    # One extra node for the control process
    assert len(job.nodes) == 1
    assert all([n.status == NodeStatus.RUNNING for n in job.nodes])


def test_scale_non_running_job_raises(mock_config, mock_spec):
    from chainsail.scheduler.errors import JobError
    from chainsail.scheduler.jobs import Job

    job = Job(
        id=1,
        spec=mock_spec,
        config=mock_config,
        node_registry={"mock": mk_mock_node_cls()},
    )

    with pytest.raises(JobError):
        job.scale_to(2)


def _add_nodes_to_job_rep(job_rep, num_nodes, num_controllers):
    from chainsail.scheduler.db import TblNodes
    from chainsail.scheduler.nodes.base import NodeStatus

    for i in range(num_nodes):
        job_rep.nodes.append(
            TblNodes(
                name=f"dummy-{i+1}",
                entrypoint="test",
                status=NodeStatus.RUNNING,
                node_type=NodeType.LIBCLOUD_VM.value,
                address=f"127.0.0.{i}",
                ports="[8080, 8081]",
                in_use=True,
                is_worker=i == 0,
            )
        )


def test_vm_job_from_db_representation(mock_config):
    # Note: this test uses a concrete Node implementation with a *Mock*
    # node driver.
    from chainsail.scheduler.db import TblJobs
    from chainsail.scheduler.errors import JobError
    from chainsail.scheduler.jobs import Job, JobStatus

    spec = """
    {
        "probability_definition": "gs://bucket/sub/path/script_and_data"
    }
    """
    mock_config.node_type = NodeType.LIBCLOUD_VM

    job_rep = TblJobs(spec=spec, status=JobStatus.RUNNING)

    # all good here
    _add_nodes_to_job_rep(job_rep, num_nodes=2, num_controllers=1)
    job = Job.from_representation(job_rep, mock_config)
    assert job.representation
    assert all([node.representation is not None for node in job.nodes])
    assert job.control_node.representation is not None

    # no controller: not good
    _add_nodes_to_job_rep(job_rep, num_nodes=2, num_controllers=0)
    with pytest.raises(JobError):
        job = Job.from_representation(job_rep, mock_config)

    # more than one controller: not good either
    _add_nodes_to_job_rep(job_rep, num_nodes=2, num_controllers=3)
    with pytest.raises(JobError):
        job = Job.from_representation(job_rep, mock_config)


def test_job_from_representation_preserves_status(mock_config):
    from chainsail.scheduler.db import TblJobs
    from chainsail.scheduler.jobs import Job, JobStatus

    # This job rep has no active nodes associated with it. This state
    # can happen once a job has been stopped since the nodes are
    # shut down and no longer in use.
    rep = TblJobs(
        spec=JobSpecSchema().dumps(JobSpec(probability_definition="foobar")),
        status=JobStatus.STOPPED,
    )

    job = Job.from_representation(
        rep, mock_config, node_registry={"mock": mk_mock_node_cls()}
    )

    assert job.status == JobStatus.STOPPED
