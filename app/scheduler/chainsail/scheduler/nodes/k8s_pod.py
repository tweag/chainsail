import logging
import os
import time
from typing import Callable, Optional, Tuple
from enum import Enum
import kubernetes as kub
from kubernetes.config import load_kube_config
from kubernetes.client import CoreV1Api, V1Pod, V1ConfigMap
from kubernetes.client.rest import ApiException
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
    while True:
        pod.refresh_status()
        if pod.status == NodeStatus.CREATING:
            time.sleep(2)
            continue
        elif pod.status == NodeStatus.RUNNING:
            return True
        elif pod.status == NodeStatus.FAILED:
            logger.error("Pod failed during its creation process.")
            return False
        else:
            logger.error(
                f"Unexpected pod status during its creation process"
                f"Pod status: {pod.status.value}"
            )
            return False


class K8sNode(Node):
    """A Chainsail node implementation which creates a Kubernetes Pod for each node."""

    NODE_TYPE = "KubernetesPod"
    _NAME_CM = "configmap-{}"
    _CM_FILE_USERCODE = "install_job_deps.sh"
    _CM_FILE_JOBSPEC = "job.json"
    _CM_FILE_SSHKEY = "authorized_keys"

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
        configmap: Optional[V1ConfigMap] = None,
        address: Optional[str] = None,
    ):
        # Names
        self._name = name
        self._name_cm = self._NAME_CM.format(name)
        # Manifests
        self._pod = pod
        self._configmap = configmap
        # Others
        self._is_controller = is_controller
        self._representation = representation
        self._config = config
        self._node_config = node_config
        self.spec = spec
        self._status = status
        self._address = address
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
                namespace=K8S_NAMESPACE, field_selector=f"involvedObject.name={self._name}"
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
                event_time, x.involved_object.kind, x.involved_object.name, x.reason, x.message
            )
        return logs

    def _read_pod(self) -> V1Pod:
        pod = self.core_v1.read_namespaced_pod(name=self._name, namespace=K8S_NAMESPACE)
        return pod

    def _all_exist(self) -> bool:
        exist = self._pod and self._configmap
        return exist

    def _any_exists(self) -> bool:
        exist = self._pod or self._configmap
        return exist

    def _create_configmap(self) -> V1ConfigMap:
        install_script_src = self._user_install_script()
        configmap = kub.client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=kub.client.V1ObjectMeta(name=self._name_cm, labels={"app": "rex"}),
            data={
                self._CM_FILE_USERCODE: install_script_src,
                self._CM_FILE_JOBSPEC: JobSpecSchema().dumps(self.spec),
                self._CM_FILE_SSHKEY: self._node_config.ssh_public_key,
            },
        )
        return configmap

    def _create_pod(self) -> V1Pod:
        ## CONTAINERS
        # TODO: Add something to replace `--log-driver=gcplogs` for every container
        # -> See this issue : https://github.com/kubernetes/kubernetes/issues/15478
        # HTTPStan Container
        httpstan_container = kub.client.V1Container(
            name="httpstan",
            image=self._config.httpstan_image,
            env=[kub.client.V1EnvVar(name="HTTPSTAN_PORT", value="8082")],
        )
        # User code container
        install_script_target = os.path.join("/chainsail", self._CM_FILE_USERCODE)
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
                    name="job-volume",
                    mount_path=install_script_target,
                    sub_path=self._CM_FILE_USERCODE,
                ),
            ],
        )
        # Worker container
        container_cmd = [self._config.cmd] + self._config.args
        container_cmd = [arg.format(job_id=self.representation.job.id) for arg in container_cmd]
        ssh_private_key_filename = os.path.basename(self._node_config.ssh_private_key_path)
        # this startup probe checks the state of the gRPC server
        startup_probe = None
        if self._is_controller:
            startup_probe = kub.client.V1Probe(
                tcp_socket=kub.client.V1TCPSocketAction(port=50051),
                period_seconds=2,
                failure_threshold=60,
            )
        container = kub.client.V1Container(
            name="rex",
            image=self._config.image,
            args=container_cmd,
            ports=[kub.client.V1ContainerPort(container_port=50051)],
            startup_probe=startup_probe,
            volume_mounts=[
                kub.client.V1VolumeMount(name="config-volume", mount_path="/chainsail"),
                kub.client.V1VolumeMount(
                    name="config-volume",
                    mount_path="/root/.ssh/id.pem",
                    sub_path=ssh_private_key_filename,
                ),
                kub.client.V1VolumeMount(
                    name="job-volume",
                    mount_path=f"/app/config/ssh/{self._CM_FILE_SSHKEY}",
                    sub_path=self._CM_FILE_SSHKEY,
                ),
                kub.client.V1VolumeMount(
                    name="job-volume",
                    mount_path=f"/chainsail-jobspec/{self._CM_FILE_JOBSPEC}",
                    sub_path=self._CM_FILE_JOBSPEC,
                ),
            ],
            resources=kub.client.V1ResourceRequirements(
                requests={
                    "cpu":self._node_config.pod_cpu, 
                    "memory":self._node_config.pod_memory,
                }
            ),
        )
        ## VOLUMES
        # User code + Job spec + SSH key volume
        job_volume = kub.client.V1Volume(
            name="job-volume", config_map=kub.client.V1ConfigMapVolumeSource(name=self._name_cm)
        )
        # Config volume
        config_volume = kub.client.V1Volume(
            name="config-volume",
            config_map=kub.client.V1ConfigMapVolumeSource(
                name=self._node_config.config_configmap_name, default_mode=0o700
            ),
        )
        ## POD
        pod = kub.client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=kub.client.V1ObjectMeta(name=self._name, labels={"app": "rex"}),
            spec=kub.client.V1PodSpec(
                containers=[httpstan_container, user_code_container, container],
                volumes=[job_volume, config_volume],
            ),
        )
        return pod

    def create(self) -> Tuple[bool, str]:
        if self._status != NodeStatus.INITIALIZED:
            raise NodeError("Attempted to created a pod which has already been created")
        logger.info("Creating pod...")
        ## CREATE RESOURCES
        self._status = NodeStatus.CREATING
        self._configmap = self._create_configmap()
        self._pod = self._create_pod()
        try:
            # Configmap
            self.core_v1.create_namespaced_config_map(
                body=self._configmap, namespace=K8S_NAMESPACE
            )
            # Pod
            self.core_v1.create_namespaced_pod(body=self._pod, namespace=K8S_NAMESPACE)
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
        if not self._all_exist():
            raise MissingNodeError
        logger.info("Restarting pod...")
        self._status = NodeStatus.RESTARTING
        try:
            self.core_v1.replace_namespaced_config_map(
                name=self._name_cm, body=self._configmap, namespace=K8S_NAMESPACE
            )
            self.core_v1.replace_namespaced_pod(
                name=self._name, body=self._pod, namespace=K8S_NAMESPACE
            )
            restarted = True
        except ApiException as e:
            logger.error(f"Failed to restart pod. Exception: {e}")
            self.refresh_status()
            restarted = False
        self.refresh_address()
        self.sync_representation()
        return restarted

    def delete(self) -> bool:
        logger.info("Deleting pod...")
        try:
            if self._pod:
                self.core_v1.delete_namespaced_pod(name=self._name, namespace=K8S_NAMESPACE)
                self._pod = None
            if self._configmap:
                self.core_v1.delete_namespaced_config_map(
                    name=self._name_cm, namespace=K8S_NAMESPACE
                )
                self._configmap = None
            self._status = NodeStatus.EXITED
            deleted = True
        except ApiException as e:
            logger.error(f"Failed to delete pod with name {self._name}. Exception: {e}")
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
        return self._address

    def refresh_address(self):
        try:
            pod = self._read_pod()
            self._address = pod.status.pod_ip
        except ApiException as e:
            logger.warning(
                f"Unable to get pod's IP address. " f"Pod name: {self._name} " f"Exception: {e}"
            )

    @property
    def status(self):
        return self._status

    def refresh_status(self):
        # See https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
        if not self._pod:
            self._status = NodeStatus.INITIALIZED
            return
        if self.status == NodeStatus.FAILED:
            return
        try:
            pod = self._read_pod()
        except Exception as e:
            logger.error(
                f"Unable to read pod status. Status not updated. "
                f"Pod name: {self._name} "
                f"Exception: {e}"
            )
            return
        phase = pod.status.phase
        ctrs_statuses = pod.status.container_statuses
        if ctrs_statuses:
            ctrs_started = all([ctr.started for ctr in ctrs_statuses])
        else:
            ctrs_started = False
        if phase == "Pending" or (phase == "Running" and not ctrs_started):
            self._status = NodeStatus.CREATING
        elif phase == "Running" and ctrs_started:
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
                pod = core_v1.read_namespaced_pod(name=name, namespace=K8S_NAMESPACE)
                configmap = core_v1.read_namespaced_config_map(
                    name=cls._NAME_CM.format(name), namespace=K8S_NAMESPACE
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
                configmap=configmap,
                address=pod.status.pod_ip,
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
