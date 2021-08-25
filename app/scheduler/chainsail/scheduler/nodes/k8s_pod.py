


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
import kubernetes as kub










class K8sNode(Node):
    """A resaas node implementation which creates a Kubernetes Pod for each node.
    
    """
    
    NODE_TYPE = "KubernetesPod"
    # NODE_TYPE = NodeType.KUBERNETES_POD
    
    
    def __init__(
        self,
        name: str,
        config: GeneralNodeConfig,
        spec: JobSpec,
        representation: Optional[TblNodes] = None,
        status: Optional[NodeStatus] = None,
    ):
        self._name = name
        self._representation = representation
        self._config = config
        self.spec = spec
        if not status:
            self._status = NodeStatus.INITIALIZED
        else:
            self._status = status
        # TODO address field
        self._address = None
        self._pod = None
    
    def create(self) -> Tuple[bool, str]:
        # TODO
        # Load kubernetes config
        kub.config.load_kub_config()
        # Define pod's containers
        httpstan_container = kub.client.V1Container(
            name="httpstan",
            image=self._config.httpstan_image,
            env=[kub.client.V1EnvVar(name='HTTPSTAN_PORT', value='8082')],
            host_network=True,
            #TODO: Add something to replace `--log-driver=gcplogs` -> See this issue : https://github.com/kubernetes/kubernetes/issues/15478
        )
        user_code_container = kub.client.V1Container(
            name="user_code",
            image=self._config.user_code_image,
            args=["python", "/app/app/user_code_server/chainsail/user_code_server/__init__.py"],
            ports=[kub.client.V1ContainerPort(container_port=50052)],
            env=[
                kub.client.V1EnvVar(name='USER_PROB_URL', value=self.spec.probability_definition),
                kub.client.V1EnvVar(name='USER_INSTALL_SCRIPT', value=None), #TODO: fill the value for install script
                kub.client.V1EnvVar(name='USER_CODE_SERVER_PORT', value=50052),
                kub.client.V1EnvVar(name='REMOTE_LOGGING_CONFIG_PATH', value='/chainsail/remote_logging.yaml'),
            ],
            volume_mounts=[
                #TODO: volume for remote_logging.yaml
                #TODO: volume for install_script
            ],
            host_network=True,
            #TODO: Add something to replace `--log-driver=gcplogs` -> See this issue : https://github.com/kubernetes/kubernetes/issues/15478
        )
        container = kub.client.V1Container(
            name="rex",
            image=self._config.image,
            args=[self._config.cmd] + self._config.args,
            ports=[kub.client.V1ContainerPort(container_port=50051)],
            volume_mounts=[
                #TODO: volume for config_dir
                #TODO: volume for authorized_keys
                #TODO: volume for pem_file
            ],
            host_network=True,
            #TODO: Add something to replace `--log-driver=gcplogs` -> See this issue : https://github.com/kubernetes/kubernetes/issues/15478
        )
        # Define pod
        self._pod = kub.client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=kub.client.V1ObjectMeta(name=self._name, labels={"app":"rex-pod"}),
            spec=kub.client.V1PodSpec(containers=[httpstan_container, user_code_container, container])
        )
        # Create pod
        core_v1 = kub.client.CoreV1Api()
        response = core_v1.create_namespaced_pod(body=self._pod, namespace="default")
        return (True, "LOGS FROM CREATE...")
    
    def restart(self) -> bool:
        # TODO
        core_v1 = kub.client.CoreV1Api()
        response = core_v1.patch_namespaced_pod(name=self._name, body=self._pod, namespace="default")
        return True
    
    def delete(self) -> bool:
        # TODO
        core_v1 = kub.client.CoreV1pi()
        response = core_v1.delete_namespaced_pod(name=self._name, namespace="default")
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
        # TODO
        return self._address

    @property
    def status(self):
        return self._status
    
    def refresh_status(self):
        # TODO
        pass
    
    @classmethod
    def from_representation(
        cls,
        spec: JobSpec,
        node_rep: TblNodes,
        scheduler_config: SchedulerConfig,
        is_controller=False,
    ) -> "Node":
        # TODO
        pass
    
    
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
        
        
        
        
        
        
        # Bind the new node to a database record if a job record was specified
        if job_rep:
            node_rep = TblNodes(in_use=True, is_worker=(not is_controller))
            job_rep.nodes.append(node_rep)
        else:
            node_rep = None
        
        node = cls(
            name=name,
            config=config,
        )
        
        # Sync over the various fields
        node.sync_representation()
        return node
    
    

    







