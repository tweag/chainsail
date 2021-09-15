import logging
import os
import time
from typing import Callable, Optional, Tuple

from chainsail.common.spec import JobSpec, JobSpecSchema
from chainsail.scheduler.config import (
    GeneralNodeConfig,
    SchedulerConfig,
    K8sNodeConfig,
    load_scheduler_config,
)
from chainsail.scheduler.db import TblJobs, TblNodes
from chainsail.scheduler.nodes.base import Node, NodeType, NodeStatus
from chainsail.scheduler.errors import (
    ConfigurationError,
    MissingNodeError,
    NodeError,
    ObjectConstructionError,
)
import kubernetes as kub
from enum import Enum


logger = logging.getLogger("chainsail.scheduler")
# Load the kubernetes config
# from the file specified by KUBECONFIG environment variable if it exists
# or from the default location $HOME/.kube/config
kub.config.load_kube_config()
core_v1 = kub.client.CoreV1Api()

DEP_INSTALL_TEMPLATE = """#!/usr/bin/env bash
set -ex
# Install dependencies (if any are provided)
{dep_install_commands}
"""
K8S_NAMESPACE = "default"


class PodStatus(Enum):
    # See https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-phase
    INITIALIZED = "Initialized"  # The pod has been specified (not a K8s pod phase)
    PENDING = "Pending"  # The pod is being created
    RUNNING = "Running"  # The pod is running
    SUCCEEDED = "Succeeded"  # All containers in the pod have terminated in success
    FAILED = "Failed"  # All containers have terminated, at least one of which in failure
    UNKNOWN = "Unknown"  # The state of the pod could not be obtained


class K8sNode(Node):
    """A resaas node implementation which creates a Kubernetes Pod for each node."""

    NODE_TYPE = "KubernetesPod"
    # NODE_TYPE = NodeType.KUBERNETES_POD

    def __init__(
        self,
        name: str,
        is_controller: bool,
        config: GeneralNodeConfig,
        node_config: K8sNodeConfig,
        spec: JobSpec,
        representation: Optional[TblNodes] = None,
        status: Optional[PodStatus] = PodStatus.INITIALIZED,
    ):
        self._name = name
        self._name_cm_usercode = f"user-dep-configmap-{self._name}"
        self._name_cm_jobspec = f"job-spec-configmap-{self._name}"
        self._name_cm_sshkey = f"ssh-key-configmap-{self._name}"
        self._is_controller = is_controller
        self._representation = representation
        self._config = config
        self._node_config = node_config
        self.spec = spec
        self._status = status
        self._address = None
        self._pod = None
        self._cm_usercode = None
        self._cm_jobspec = None
        self._cm_sshkey = None

    def _user_install_script(self) -> str:
        install_commands = "\n".join([d.installation_script for d in self.spec.dependencies])
        script = DEP_INSTALL_TEMPLATE.format(dep_install_commands=install_commands)
        return script

    def create(self) -> Tuple[bool, str]:
        if self._status != PodStatus.INITIALIZED:
            raise NodeError("Attempted to created a pod which has already been created")
        logger.info("Creating pod...")
        ## CONFIGMAPS
        # User code configmap
        install_script_name = "install_job_deps.sh"
        install_script_src = self._user_install_script()
        self._cm_usercode = kub.client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=kub.client.V1ObjectMeta(name=self._name_cm_usercode, labels={"app": "rex"}),
            data={install_script_name: install_script_src},
        )
        # Job spec configmap
        job_spec_filename = "job.json"
        self._cm_jobspec = kub.client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=kub.client.V1ObjectMeta(name=self._name_cm_jobspec, labels={"app": "rex"}),
            data={job_spec_filename: JobSpecSchema().dumps(self.spec)},
        )
        # Public ssh key configmap
        ssh_key_filename = "authorized_keys"
        self._cm_sshkey = kub.client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=kub.client.V1ObjectMeta(name=self._name_cm_sshkey, labels={"app": "rex"}),
            data={ssh_key_filename: self._node_config.ssh_public_key},
        )
        ## CONTAINERS
        # HTTPStan Container
        httpstan_container = kub.client.V1Container(
            name="httpstan",
            image=self._config.httpstan_image,
            env=[kub.client.V1EnvVar(name="HTTPSTAN_PORT", value="8082")],
            # TODO: Add something to replace `--log-driver=gcplogs` -> See this issue : https://github.com/kubernetes/kubernetes/issues/15478
        )
        # User code container
        install_script_target = os.path.join("/chainsail", install_script_name)
        user_code_container = kub.client.V1Container(
            name="user-code",
            image=self._config.user_code_image,
            args=["python", "/app/app/user_code_server/chainsail/user_code_server/__init__.py"],
            ports=[kub.client.V1ContainerPort(container_port=50052)],
            env=[
                kub.client.V1EnvVar(name="USER_PROB_URL", value=self.spec.probability_definition),
                kub.client.V1EnvVar(name="USER_INSTALL_SCRIPT", value=install_script_target),
                kub.client.V1EnvVar(name="USER_CODE_SERVER_PORT", value="50052"),
                kub.client.V1EnvVar(
                    name="REMOTE_LOGGING_CONFIG_PATH", value="/chainsail/remote_logging.yaml"
                ),
            ],
            volume_mounts=[
                kub.client.V1VolumeMount(
                    name="config-volume",
                    mount_path="/chainsail/remote_logging.yaml",
                    sub_path="remote_logging.yaml",
                ),
                kub.client.V1VolumeMount(
                    name="user-dep",
                    mount_path=install_script_target,
                    sub_path=install_script_name,
                ),
            ],
            # TODO: Add something to replace `--log-driver=gcplogs` -> See this issue : https://github.com/kubernetes/kubernetes/issues/15478
        )
        # Worker container
        container_cmd = [self._config.cmd] + self._config.args
        container_cmd = [arg.format(job_id=self.representation.job.id) for arg in container_cmd]
        ssh_private_key_filename = os.path.basename(self._node_config.ssh_private_key_path)
        container = kub.client.V1Container(
            name="rex",
            image=self._config.image,
            args=container_cmd,
            ports=[kub.client.V1ContainerPort(container_port=50051)],
            volume_mounts=[
                kub.client.V1VolumeMount(
                    name="config-volume",
                    mount_path="/chainsail",
                ),
                kub.client.V1VolumeMount(
                    name="config-volume",
                    mount_path="/root/.ssh/id.pem",
                    sub_path=ssh_private_key_filename,
                ),
                kub.client.V1VolumeMount(
                    name="ssh-key",
                    mount_path=f"/app/config/ssh/{ssh_key_filename}",
                    sub_path=ssh_key_filename,
                ),
                kub.client.V1VolumeMount(
                    name="job-spec",
                    mount_path=f"/chainsail-bis/{job_spec_filename}",
                    sub_path=job_spec_filename,
                ),
            ],
            # TODO: Add something to replace `--log-driver=gcplogs` -> See this issue : https://github.com/kubernetes/kubernetes/issues/15478
        )
        ## VOLUMES
        # User code volume
        user_code_volume = kub.client.V1Volume(
            name="user-dep",
            config_map=kub.client.V1ConfigMapVolumeSource(name=self._name_cm_usercode),
        )
        # Job spec volume
        job_spec_volume = kub.client.V1Volume(
            name="job-spec",
            config_map=kub.client.V1ConfigMapVolumeSource(name=self._name_cm_jobspec),
        )
        # Public ssh key volume
        ssh_key_volume = kub.client.V1Volume(
            name="ssh-key",
            config_map=kub.client.V1ConfigMapVolumeSource(name=self._name_cm_sshkey),
        )
        # Config volume
        config_volume = kub.client.V1Volume(
            name="config-volume",
            config_map=kub.client.V1ConfigMapVolumeSource(
                name=self._node_config.config_configmap_name, default_mode=0o700
            ),
        )
        ## POD
        self._pod = kub.client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=kub.client.V1ObjectMeta(name=self._name, labels={"app": "rex"}),
            spec=kub.client.V1PodSpec(
                containers=[httpstan_container, user_code_container, container],
                volumes=[user_code_volume, job_spec_volume, ssh_key_volume, config_volume],
            ),
        )
        ##  CREATE RESOURCES
        # Configmaps
        _ = core_v1.create_namespaced_config_map(body=self._cm_usercode, namespace=K8S_NAMESPACE)
        _ = core_v1.create_namespaced_config_map(body=self._cm_jobspec, namespace=K8S_NAMESPACE)
        _ = core_v1.create_namespaced_config_map(body=self._cm_sshkey, namespace=K8S_NAMESPACE)
        # Pod
        _ = core_v1.create_namespaced_pod(body=self._pod, namespace=K8S_NAMESPACE)
        self.refresh_status()
        self.refresh_address()
        self.sync_representation()
        # Wait for all resources to be created
        while (
            self._status == PodStatus.INITIALIZED
            or self._status == PodStatus.PENDING
            or not self._address
        ):
            time.sleep(3)
            self.refresh_status()
            self.refresh_address()
            self.sync_representation()
        # Wait for the pods to initialize properly
        # TODO: This should be handled using k8s liveness/startup/readiness probes
        if self._is_controller:
            time.sleep(20)
        else:
            time.sleep(10)
        return (True, "LOGS FROM CREATE...")

    def restart(self) -> bool:
        if not self._pod:
            raise MissingNodeError
        logger.info("Restarting pod...")
        _ = core_v1.patch_namespaced_config_map(
            name=self._name_cm_usercode, body=self._cm_usercode, namespace=K8S_NAMESPACE
        )
        _ = core_v1.patch_namespaced_config_map(
            name=self._name_cm_jobspec, body=self._cm_jobspec, namespace=K8S_NAMESPACE
        )
        _ = core_v1.patch_namespaced_config_map(
            name=self._name_cm_sshkey, body=self._cm_sshkey, namespace=K8S_NAMESPACE
        )
        _ = core_v1.patch_namespaced_pod(name=self._name, body=self._pod, namespace=K8S_NAMESPACE)
        self.refresh_status()
        self.refresh_address()
        self.sync_representation()
        return True

    def delete(self) -> bool:
        if not self._pod:
            return True
        logger.info("Deleting pod...")
        _ = core_v1.delete_namespaced_pod(name=self._name, namespace=K8S_NAMESPACE)
        _ = core_v1.delete_namespaced_config_map(
            name=self._name_cm_usercode, namespace=K8S_NAMESPACE
        )
        _ = core_v1.delete_namespaced_config_map(
            name=self._name_cm_jobspec, namespace=K8S_NAMESPACE
        )
        _ = core_v1.delete_namespaced_config_map(
            name=self._name_cm_sshkey, namespace=K8S_NAMESPACE
        )
        self.refresh_status()
        self.sync_representation()
        return True

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

    def refresh_address(self):
        try:
            pod = core_v1.read_namespaced_pod(name=self._name, namespace=K8S_NAMESPACE)
            self._address = pod.status.pod_ip
        except Exception as e:
            logger.error(f"Unable to get pod's IP address. Exception: {e}")

    @property
    def status(self):
        return self._status

    def refresh_status(self):
        if not self._pod:
            self._status = PodStatus.INITIALIZED
            return
        if self.status == PodStatus.FAILED:
            return
        try:
            pod = core_v1.read_namespaced_pod(name=self._name, namespace=K8S_NAMESPACE)
            phase = pod.status.phase
        except Exception as e:
            logger.error(f"Unable to read pod status. Status not updated. Exception: {e}")
            return
        if phase == "Pending":
            self._status = PodStatus.PENDING
        elif phase == "Running":
            self._status = PodStatus.RUNNING
        elif phase == "Succeeded":
            self._status = PodStatus.SUCCEEDED
        elif phase == "Failed":
            self._status = PodStatus.FAILED
        elif phase == "Unknown":
            self._status = PodStatus.UNKNOWN

    @classmethod
    def from_representation(
        cls,
        spec: JobSpec,
        node_rep: TblNodes,
        scheduler_config: SchedulerConfig,
        is_controller=False,
    ) -> "Node":
        node_config: K8sNodeConfig = scheduler_config.node_config
        if is_controller:
            config = scheduler_config.controller
        else:
            config = scheduler_config.worker
        # If the pod has only been initialized, no actual compute resource
        # has been created yet
        if node_rep.status == PodStatus.INITIALIZED:
            name = node_rep.name
        # Otherwise we can look up the compute resource
        else:
            try:
                node = core_v1.read_namespaced_pod(name=node_rep.name, namespace=K8S_NAMESPACE)
                name = node.metadata.name
            except Exception:
                raise ObjectConstructionError(
                    f"Failed to find an existing pod with name "
                    f"{node_rep.name} job: {node_rep.job_id}, node: {node_rep.id}"
                )
        return cls(
            name=name,
            is_controller=is_controller,
            config=config,
            node_config=node_config,
            spec=spec,
            status=PodStatus(node_rep.status),
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
        node_config: K8sNodeConfig = scheduler_config.node_config
        if is_controller:
            config = scheduler_config.controller
        else:
            config = scheduler_config.worker
        # Bind the new node(=pod) to a database record if a job record was specified
        if job_rep:
            node_rep = TblNodes(in_use=True, is_worker=(not is_controller))
            job_rep.nodes.append(node_rep)
        else:
            node_rep = None
        node = cls(
            name=name,
            is_controller=is_controller,
            config=config,
            node_config=node_config,
            spec=spec,
            representation=node_rep,
        )
        # Sync over the various fields
        node.sync_representation()
        return node
