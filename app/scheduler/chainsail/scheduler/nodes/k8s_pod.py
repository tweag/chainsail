import logging
import os
import time
from typing import Callable, Optional, Tuple
from enum import Enum
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
from kubernetes.config import load_kube_config
from kubernetes.client import CoreV1Api, V1Pod, V1ConfigMap
from kubernetes.client.rest import ApiException


logger = logging.getLogger("chainsail.scheduler")

DEP_INSTALL_TEMPLATE = """#!/usr/bin/env bash
set -ex
# Install dependencies (if any are provided)
{dep_install_commands}
"""
K8S_NAMESPACE = "default"


def monitor_deployment(pod: "K8sNode") -> bool:
    """Monitor the proper creation and startup of a pod.

    Args:
        pod: The pod instance to monitor

    Returns:
        A boolean indicating the success or failure of the pod creation
    """
    # TODO: Currently cannot use `refresh_status` because it is flawed (see
    # the method comments for details) => using the Pod's phase instead. When
    # it will be fixed, change to using `refresh_status` because it makes more
    # sense
    phase = pod._read_pod().status.phase
    while True:
        # Wait for the pod to be running (meaning all containers are running)
        if phase == "Pending":
            time.sleep(2)
            phase = pod._read_pod().status.phase
            continue
        # Wait for all the containers to be fully ready
        elif phase == "Running":
            # TODO: Use K8s *readiness probes* to monitor readiness
            if pod._is_controller:
                time.sleep(30)
            else:
                time.sleep(0)
            return True
        # Unusual cases
        elif phase == "":
            logger.error("Pod failed during its creation process.")
            return False
        else:
            logger.error("Unexpected pod status during its creation process")
            return False


class K8sNode(Node):
    """A resaas node implementation which creates a Kubernetes Pod for each node."""

    NODE_TYPE = "KubernetesPod"
    _NAME_CM_USERCODE = "user-dep-configmap-{}"
    _NAME_CM_JOBSPEC = "job-spec-configmap-{}"
    _NAME_CM_SSHKEY = "ssh-key-configmap-{}"

    def __init__(
        self,
        name: str,
        is_controller: bool,
        config: GeneralNodeConfig,
        node_config: K8sNodeConfig,
        spec: JobSpec,
        representation: Optional[TblNodes] = None,
        status: Optional[NodeStatus] = NodeStatus.INITIALIZED,
        # If creating from existing resources, can specify the k8s objects
        pod: Optional[V1Pod] = None,
        cm_usercode: Optional[V1ConfigMap] = None,
        cm_jobspec: Optional[V1ConfigMap] = None,
        cm_sshkey: Optional[V1ConfigMap] = None,
    ):
        # Names
        self._name = name
        self._name_cm_usercode = self._NAME_CM_USERCODE.format(name)
        self._name_cm_jobspec = self._NAME_CM_JOBSPEC.format(name)
        self._name_cm_sshkey = self._NAME_CM_SSHKEY.format(name)
        # Manifests
        self._pod = pod
        self._cm_usercode = cm_usercode
        self._cm_jobspec = cm_jobspec
        self._cm_sshkey = cm_sshkey
        # Others
        self._is_controller = is_controller
        self._representation = representation
        self._config = config
        self._node_config = node_config
        self.spec = spec
        self._status = status
        self._address = None
        # Load the kubernetes config:
        # - Either from the file specified by KUBECONFIG environment variable if it exists
        # - Or from the default location $HOME/.kube/config
        load_kube_config()
        self.core_v1 = CoreV1Api()

    def _user_install_script(self) -> str:
        install_commands = "\n".join([d.installation_script for d in self.spec.dependencies])
        script = DEP_INSTALL_TEMPLATE.format(dep_install_commands=install_commands)
        return script

    def _get_logs(self) -> str:
        try:
            events = self.core_v1.list_namespaced_event(
                namespace=K8S_NAMESPACE,
                field_selector=f"involvedObject.name={self._name}",
            )
        except ApiException as e:
            logger.warning("Unable to fetch pod events. Exception: {e}")
            return ""
        logs = ""
        for x in events.items:
            if x.event_time:
                event_time = x.event_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            elif x.first_timestamp:
                event_time = x.first_timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
            else:
                event_time = "unknown event time"
            logs += "{:23}   {}   {}   {:10}   {}\n".format(
                event_time,
                x.involved_object.kind,
                x.involved_object.name,
                x.reason,
                x.message,
            )
        return logs

    def _read_pod(self) -> V1Pod:
        pod = self.core_v1.read_namespaced_pod(
            name=self._name,
            namespace=K8S_NAMESPACE,
        )
        return pod

    def create(self) -> Tuple[bool, str]:
        if self._status != NodeStatus.INITIALIZED:
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
        ## CREATE RESOURCES
        self._status = NodeStatus.CREATING
        try:
            # Configmaps
            _ = self.core_v1.create_namespaced_config_map(
                body=self._cm_usercode,
                namespace=K8S_NAMESPACE,
            )
            _ = self.core_v1.create_namespaced_config_map(
                body=self._cm_jobspec,
                namespace=K8S_NAMESPACE,
            )
            _ = self.core_v1.create_namespaced_config_map(
                body=self._cm_sshkey,
                namespace=K8S_NAMESPACE,
            )
            # Pod
            _ = self.core_v1.create_namespaced_pod(
                body=self._pod,
                namespace=K8S_NAMESPACE,
            )
        except ApiException as e:
            self._status = NodeStatus.FAILED
            logs = self._get_logs()
            self.sync_representation()
            return (False, logs)
        ## MONITOR CREATION
        ready = monitor_deployment(self)
        if ready:
            self._status = NodeStatus.RUNNING
        else:
            self._status = NodeStatus.FAILED
        logs = self._get_logs()
        self.refresh_address()
        self.sync_representation()
        return (ready, logs)

    def restart(self) -> bool:
        if not self._pod or not self._cm_usercode or not self._cm_jobspec or not self._cm_sshkey:
            raise MissingNodeError
        logger.info("Restarting pod...")
        try:
            _ = self.core_v1.replace_namespaced_config_map(
                name=self._name_cm_usercode,
                body=self._cm_usercode,
                namespace=K8S_NAMESPACE,
            )
            _ = self.core_v1.replace_namespaced_config_map(
                name=self._name_cm_jobspec,
                body=self._cm_jobspec,
                namespace=K8S_NAMESPACE,
            )
            _ = self.core_v1.replace_namespaced_config_map(
                name=self._name_cm_sshkey,
                body=self._cm_sshkey,
                namespace=K8S_NAMESPACE,
            )
            _ = self.core_v1.replace_namespaced_pod(
                name=self._name,
                body=self._pod,
                namespace=K8S_NAMESPACE,
            )
            self._status = NodeStatus.RESTARTING
            restarted = True
        except ApiException as e:
            logger.error(f"Failed to restart pod. Exception: {e}")
            restarted = False
        self.refresh_address()
        self.sync_representation()
        return restarted

    def delete(self) -> bool:
        if (
            not self._pod
            and not self._cm_usercode
            and not self._cm_jobspec
            and not self._cm_sshkey
        ):
            return True
        try:
            logger.info("Deleting pod...")
            _ = self.core_v1.delete_namespaced_pod(
                name=self._name,
                namespace=K8S_NAMESPACE,
            )
            _ = self.core_v1.delete_namespaced_config_map(
                name=self._name_cm_usercode,
                namespace=K8S_NAMESPACE,
            )
            _ = self.core_v1.delete_namespaced_config_map(
                name=self._name_cm_jobspec,
                namespace=K8S_NAMESPACE,
            )
            _ = self.core_v1.delete_namespaced_config_map(
                name=self._name_cm_sshkey,
                namespace=K8S_NAMESPACE,
            )
            self._status = NodeStatus.EXITED
            deleted = True
        except ApiException as e:
            logger.error(f"Failed to delete pod. Exception: {e}")
            self.refresh_status()
            deleted = False
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
        self.refresh_address()
        return self._address

    def refresh_address(self):
        try:
            pod = self._read_pod()
            self._address = pod.status.pod_ip
        except ApiException as e:
            logger.warning(f"Unable to get pod's IP address. Exception: {e}")

    @property
    def status(self):
        return self._status

    def refresh_status(self):
        # See https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-phase
        # TODO: The NodeStatus.Running status is currently not accurate. Should be:
        # - if (phase=="Pending") or (phase=="Running" and not READY) -> NodeStatus.CREATING
        # - if (phase=="Running" and READY) -> NodeStatus.RUNNING
        # where READY is some kind of test of the readiness of the containers (use *readiness probes*)
        if not self._pod:
            self._status = NodeStatus.INITIALIZED
            return
        if self.status == NodeStatus.FAILED:
            return
        try:
            pod = self._read_pod()
            phase = pod.status.phase
        except Exception as e:
            logger.error(f"Unable to read pod status. Status not updated. Exception: {e}")
            return
        if phase == "Pending":
            self._status = NodeStatus.CREATING
        elif phase == "Running":
            self._status = NodeStatus.RUNNING
        elif phase == "Succeeded":
            self._status = NodeStatus.EXITED
        elif phase == "Failed":
            self._status = NodeStatus.FAILED
        elif phase == "Unknown":
            self._status = NodeStatus.UNKNOWN

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
        # If the node has only been initialized, no actual compute resource
        # has been created yet
        if node_rep.status == NodeStatus.INITIALIZED:
            name = node_rep.name
            return cls(
                name=name,
                is_controller=is_controller,
                config=config,
                node_config=node_config,
                spec=spec,
                representation=node_rep,
            )
        # Otherwise we can look up the compute resources
        else:
            try:
                load_kube_config()
                core_v1 = CoreV1Api()
                name = node_rep.name
                pod = core_v1.read_namespaced_pod(
                    name=name,
                    namespace=K8S_NAMESPACE,
                )
                cm_usercode = core_v1.read_namespaced_config_map(
                    name=cls._NAME_CM_USERCODE.format(name),
                    namespace=K8S_NAMESPACE,
                )
                cm_jobspec = core_v1.read_namespaced_config_map(
                    name=cls._NAME_CM_JOBSPEC.format(name),
                    namespace=K8S_NAMESPACE,
                )
                cm_sshkey = core_v1.read_namespaced_config_map(
                    name=cls._NAME_CM_SSHKEY.format(name),
                    namespace=K8S_NAMESPACE,
                )
            except ApiException as e:
                raise ObjectConstructionError(
                    f"Failed to find an existing pod (or one of its dependency configmap) with name "
                    f"{node_rep.name} job: {node_rep.job_id}, node: {node_rep.id}"
                ) from e
            return cls(
                name=name,
                is_controller=is_controller,
                config=config,
                node_config=node_config,
                spec=spec,
                representation=node_rep,
                status=NodeStatus(node_rep.status),
                pod=pod,
                cm_usercode=cm_usercode,
                cm_jobspec=cm_jobspec,
                cm_sshkey=cm_sshkey,
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
