from unittest.mock import Mock, patch
import pytest
from chainsail.common.spec import JobSpec
from chainsail.scheduler.config import GeneralNodeConfig, SchedulerConfig, K8sNodeConfig
from chainsail.scheduler.nodes.base import NodeType, NodeStatus


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
    node_config = K8sNodeConfig(
        "fake-configmap-name",
        "xxxxxxxxxxxxx",
        "path/to/key.pem",
        "foo/controller.yaml",
        "foo/storage.yaml",
    )
    scheduler_config = SchedulerConfig(
        controller=config,
        worker=config,
        node_type=NodeType.KUBERNETES_POD,
        node_config=node_config,
        results_url_expiry_time=42,
        remote_logging_config_path=None,
    )
    return scheduler_config


# @patch("kubernetes.config.load_kube_config")
# @patch("kubernetes.client.CoreV1Api")
# def test_k8s_node_from_representation(mock_scheduler_config):
#     from chainsail.common.spec import JobSpec
#     from chainsail.scheduler.db import TblNodes
#     from chainsail.scheduler.nodes.base import NodeType, NodeStatus
#     from chainsail.scheduler.nodes.k8s_pod import K8sNode

#     job_spec = JobSpec("gs://my-bucket/scripts")
#     node_rep = TblNodes(
#         id=1,
#         job_id=1,
#         name="dummy-1",
#         node_type=NodeType.KUBERNETES_POD,
#         entrypoint="echo 'hello world'",
#         status=NodeStatus.RUNNING,
#         address="127.0.0.1",
#         ports="[8080]",
#     )

#     node = K8sNode.from_representation(job_spec, node_rep, mock_scheduler_config)
#     # This method should bind node_rep to the new node
#     assert node.representation


# @patch("kubernetes.config.load_kube_config")
# def test_k8s_node_from_config_with_job(mock_scheduler_config):
#     from chainsail.common.spec import JobSpec
#     from chainsail.scheduler.db import TblJobs
#     from chainsail.scheduler.nodes.k8s_pod import K8sNode

#     job_spec = JobSpec("gs://my-bucket/scripts")
#     node = K8sNode.from_config("dummy-1", mock_scheduler_config, job_spec, job_rep=TblJobs(id=1))
#     assert node.representation
#     assert node.representation.job.id == 1


# @patch("kubernetes.client.CoreV1Api")
# def test_k8s_node_from_representation_then_create(mock_scheduler_config):
#     from chainsail.common.spec import JobSpec, PipDependencies
#     from chainsail.scheduler.db import TblJobs, TblNodes
#     from chainsail.scheduler.nodes.base import NodeType, NodeStatus
#     from chainsail.scheduler.nodes.k8s_pod import K8sNode

#     job_spec = JobSpec("gs://my-bucket/scripts", dependencies=[PipDependencies(["numpy"])])
#     node_rep = TblNodes(
#         id=1,
#         job_id=1,
#         name="new-node",
#         node_type=NodeType.KUBERNETES_POD,
#         entrypoint="echo 'hello world'",
#         # This node has not been actually created yet
#         status=NodeStatus.INITIALIZED,
#         job=TblJobs(),
#     )

#     # Create the node object
#     node = K8sNode.from_representation(
#         job_spec,
#         node_rep,
#         mock_scheduler_config,
#     )
#     node.refresh_status()
#     (is_created, _) = node.create()

#     assert is_created
#     assert node.status == NodeStatus.RUNNING


# def test_k8s_node_lifecycle(mock_scheduler_config):
#     from chainsail.common.spec import JobSpec
#     from chainsail.scheduler.nodes.base import NodeStatus
#     from chainsail.scheduler.nodes.k8s_pod import K8sNode

#     job_spec = JobSpec("gs://my-bucket/scripts")

#     with patch("chainsail.scheduler.nodes.k8s_pod.create_resources"):
#         node = K8sNode(
#             name="test",
#             is_controller=True,
#             config=mock_scheduler_config.controller,
#             node_config=mock_scheduler_config.node_config,
#             spec=job_spec,
#         )

#         statuses = [node.status]
#         is_created, _ = node.create()
#         statuses.append(node.status)
#         is_restarted = node.restart()
#         statuses.append(node.status)
#         is_deleted = node.delete()
#         statuses.append(node.status)

#     # Check that all operations succeeded
#     assert all([is_created, is_restarted, is_deleted])
#     # If so, the following statuses should have been observed:
#     assert statuses == [
#         NodeStatus.INITIALIZED,
#         NodeStatus.RUNNING,
#         NodeStatus.RESTARTING,
#         NodeStatus.EXITED,
#     ]
