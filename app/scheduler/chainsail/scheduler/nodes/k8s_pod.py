import logging
import os
import time
from enum import Enum
from typing import Callable, Optional, Tuple

import kubernetes as kub
from chainsail.common.spec import JobSpec, JobSpecSchema
from chainsail.scheduler.config import (
    GeneralNodeConfig,
    K8sNodeConfig,
    SchedulerConfig,
    load_scheduler_config,
)
from chainsail.scheduler.db import TblJobs, TblNodes
from chainsail.scheduler.errors import (
    ConfigurationError,
    MissingNodeError,
    NodeError,
    ObjectConstructionError,
)
from chainsail.scheduler.nodes.base import Node, NodeStatus, NodeType
from kubernetes.client import (
    V1ConfigMap,
    V1KeyToPath,
    V1ObjectMeta,
    V1Pod,
    V1Service,
    V1ServicePort,
    V1ServiceSpec,
    V1Volume,
)
from kubernetes.client.rest import ApiException

logger = logging.getLogger("chainsail.scheduler")

DEP_INSTALL_TEMPLATE = """#!/usr/bin/env bash
set -ex
# Install dependencies (if any are provided)
{dep_install_commands}
"""
K8S_NAMESPACE = "default"
K8S_SSH_PUB_KEY = "pub"
K8S_SSH_PEM_KEY = "pem"
K8S_SSH_PEM_KEY_FILE = "id.pem"
PORT_RANGE_MIN = 4000


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


def service_fqdn(svc_name: str) -> str:
    return f"{svc_name}.{K8S_NAMESPACE}.svc.cluster.local"


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
        service: Optional[V1Service] = None,
        configmap: Optional[V1ConfigMap] = None,
        address: Optional[str] = None,
    ):
        # Names
        self._name = name
        self._name_cm = self._NAME_CM.format(name)
        # Manifests
        self._pod = pod
        self._service = service
        self._configmap = configmap
        # Others
        self._is_controller = is_controller
        self._representation = representation
        self._config = config
        self._node_config = node_config
        self.spec = spec
        self._status = status
        self._address = address
        self.api = node_config.create_node_driver()

    def _user_install_script(self) -> str:
        install_commands = "\n".join([d.installation_script for d in self.spec.dependencies])
        script = DEP_INSTALL_TEMPLATE.format(dep_install_commands=install_commands)
        return script

    def _get_logs(self) -> str:
        try:
            events = self.api.list_namespaced_event(
                namespace=K8S_NAMESPACE,
                field_selector=f"involvedObject.name={self._name}",
            )
        except ApiException as e:
            logger.warning(f"Unable to fetch pod events. Exception: {e}")
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
        pod = self.api.read_namespaced_pod(name=self._name, namespace=K8S_NAMESPACE)
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
            image_pull_policy=self._node_config.image_pull_policy,
        )
        # User code container
        install_script_target = os.path.join("/chainsail", self._CM_FILE_USERCODE)
        user_code_container = kub.client.V1Container(
            name="user-code",
            image=self._config.user_code_image,
            image_pull_policy=self._node_config.image_pull_policy,
            args=[
                "python",
                "/app/app/user_code_server/chainsail/user_code_server/__init__.py",
            ],
            ports=[kub.client.V1ContainerPort(container_port=50052)],
            env=[
                kub.client.V1EnvVar(name="USER_PROB_URL", value=self.spec.probability_definition),
                kub.client.V1EnvVar(name="USER_INSTALL_SCRIPT", value=install_script_target),
                kub.client.V1EnvVar(name="USER_CODE_SERVER_PORT", value="50052"),
                kub.client.V1EnvVar(
                    name="REMOTE_LOGGING_CONFIG_PATH",
                    value="/chainsail/remote_logging.yaml",
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
        # this startup probe checks the state of the gRPC server
        if self._is_controller:
            startup_probe = kub.client.V1Probe(
                tcp_socket=kub.client.V1TCPSocketAction(port=50051),
                period_seconds=2,
                failure_threshold=60,
            )
        # startup probe for workers checks the state of the ssh server
        else:
            startup_probe = kub.client.V1Probe(
                tcp_socket=kub.client.V1TCPSocketAction(port=26),
                period_seconds=2,
                failure_threshold=60,
            )
        container = kub.client.V1Container(
            name="rex",
            image=self._config.image,
            image_pull_policy=self._node_config.image_pull_policy,
            args=container_cmd,
            ports=[kub.client.V1ContainerPort(container_port=50051)],
            startup_probe=startup_probe,
            volume_mounts=[
                kub.client.V1VolumeMount(name="config-volume", mount_path="/chainsail"),
                kub.client.V1VolumeMount(name="ssh-volume", mount_path="/root/.ssh"),
                kub.client.V1VolumeMount(
                    name="job-volume",
                    mount_path=f"/chainsail-jobspec/{self._CM_FILE_JOBSPEC}",
                    sub_path=self._CM_FILE_JOBSPEC,
                ),
            ],
            resources=kub.client.V1ResourceRequirements(
                requests={
                    "cpu": self._node_config.pod_cpu,
                    "memory": self._node_config.pod_memory,
                }
            ),
        )
        ## VOLUMES
        # User code + Job spec
        job_volume = kub.client.V1Volume(
            name="job-volume",
            config_map=kub.client.V1ConfigMapVolumeSource(name=self._name_cm),
        )
        # SSH key volume
        ssh_volume = V1Volume(
            name="ssh-volume",
            secret=kub.client.V1SecretVolumeSource(
                secret_name=self._node_config.ssh_key_secret,
                default_mode=0o600,
                items=[
                    V1KeyToPath(key=K8S_SSH_PUB_KEY, path=self._CM_FILE_SSHKEY, mode=0o400),
                    V1KeyToPath(key=K8S_SSH_PEM_KEY, path=K8S_SSH_PEM_KEY_FILE, mode=0o400),
                ],
            ),
        )
        # Config volume
        config_volume = kub.client.V1Volume(
            name="config-volume",
            config_map=kub.client.V1ConfigMapVolumeSource(
                name=self._node_config.config_configmap_name, default_mode=0o600
            ),
        )
        ## POD
        pod = kub.client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=kub.client.V1ObjectMeta(
                name=self._name, labels={"app": "rex", "node_name": self._name}
            ),
            spec=kub.client.V1PodSpec(
                # Note: we don't want k8s to restart this pod since chainsail handles retries internally
                restart_policy="Never",
                containers=[httpstan_container, user_code_container, container],
                volumes=[job_volume, config_volume, ssh_volume],
                tolerations=[kub.client.V1Toleration(key="app", value="chainsail")],
            ),
        )
        # TODO: Expose distinct ports for controller / worker nodes
        service = V1Service(
            metadata=V1ObjectMeta(name=self._name),
            spec=V1ServiceSpec(
                selector={"node_name": self._name},
                ports=[
                    V1ServicePort(name="controller-grpc", port=50051),
                    V1ServicePort(name="openmpi-oob", port=3999),
                    V1ServicePort(name="openmpi-ssh", port=26),
                ]
                # Need to expose ports for each node in the network
                + [
                    V1ServicePort(
                        name=f"openmpi-btl-{PORT_RANGE_MIN + i}",
                        port=PORT_RANGE_MIN + i,
                    )
                    for i in range(0, self._config.max_nodes_per_job)
                ],
            ),
        )
        return pod, service

    def create(self) -> Tuple[bool, str]:
        if self._status != NodeStatus.INITIALIZED:
            raise NodeError("Attempted to created a pod which has already been created")
        logger.info("Creating pod...")
        ## CREATE RESOURCES
        self._status = NodeStatus.CREATING
        self._configmap = self._create_configmap()
        self._pod, self._service = self._create_pod()
        try:
            # Configmap
            self.api.create_namespaced_config_map(body=self._configmap, namespace=K8S_NAMESPACE)
            # Pod
            self.api.create_namespaced_pod(body=self._pod, namespace=K8S_NAMESPACE)
            # Service
            self.api.create_namespaced_service(body=self._service, namespace=K8S_NAMESPACE)
        except ApiException as e:
            logger.exception(e)
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
            self.api.replace_namespaced_config_map(
                name=self._name_cm, body=self._configmap, namespace=K8S_NAMESPACE
            )
            self.api.replace_namespaced_pod(
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
                self.api.delete_namespaced_pod(name=self._name, namespace=K8S_NAMESPACE)
                self._pod = None
            if self._configmap:
                self.api.delete_namespaced_config_map(name=self._name_cm, namespace=K8S_NAMESPACE)
                self._configmap = None
            if self._service:
                self.api.delete_namespaced_service(name=self._name, namespace=K8S_NAMESPACE)
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
            self._address = service_fqdn(pod.metadata.name)
        except ApiException as e:
            logger.warning(
                f"Unable to get pod's address. " f"Pod name: {self._name} " f"Exception: {e}"
            )

    @property
    def status(self):
        return self._status

    def refresh_status(self):
        # See https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
        if not self._pod:
            # TODO: Can we remove this status update here?
            self._status = NodeStatus.INITIALIZED
            return
        if self.status == NodeStatus.FAILED:
            return
        pod = self._read_pod()
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
                api = node_config.create_node_driver()
                name = node_rep.name
                pod = api.read_namespaced_pod(name=name, namespace=K8S_NAMESPACE)
                service = api.read_namespaced_service(name=name, namespace=K8S_NAMESPACE)
                configmap = api.read_namespaced_config_map(
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
                service=service,
                configmap=configmap,
                address=service_fqdn(pod.metadata.name),
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
