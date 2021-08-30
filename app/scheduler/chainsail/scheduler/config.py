"""
Scheduler app configuration file parsing
"""
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml
from libcloud.compute.base import NodeDriver
from libcloud.compute.providers import Provider, get_driver
from marshmallow import Schema, fields
from marshmallow.decorators import post_load
from marshmallow.exceptions import ValidationError
from marshmallow_enum import EnumField
from chainsail.scheduler.errors import ConfigurationError
from chainsail.scheduler.nodes.base import NodeType
from chainsail.scheduler.nodes.mock import DeployableDummyNodeDriver


def lookup_driver_cls(provider_name: str) -> type:
    """Looks up the libcloud driver using its libcloud provider name (case-sensitive). Also
    supports the 'CHAINSAIL_DUMMY' driver.

    Args:
        provider_name: The provider attribute name. See `libcloud.compute.providers.Provider`
            for a full list of options.

    Returns:
        The matching NodeDriver class

    Raises:
        ConfigurationError: If the provider name does not match any known providers.
    """
    if provider_name == "CHAINSAIL_DUMMY":
        return DeployableDummyNodeDriver
    else:
        try:
            provider = getattr(Provider, provider_name)
        except AttributeError:
            raise ConfigurationError(f"Unrecognized libcloud provider name: '{provider_name}'")
        return get_driver(provider)


class HasDriver(ABC):
    @abstractmethod
    def create_node_driver(self) -> Any:
        """Creates a driver object which can be used to run a node"""
        pass


@dataclass
class VMNodeConfig(HasDriver):
    """Configurations for a `VMNode`"""

    vm_image_id: str
    vm_size: str
    ssh_user: str
    ssh_public_key: str
    ssh_private_key_path: str
    controller_config_path: str
    storage_config_path: str
    libcloud_driver: NodeDriver
    libcloud_driver_inputs: Dict
    libcloud_create_node_inputs: Dict
    init_script: str = ""

    def create_node_driver(self):
        return self.libcloud_driver(**self.libcloud_driver_inputs)


class VMNodeConfigSchema(Schema):
    # The image id
    vm_image_id = fields.String(required=True)
    # The vm size
    vm_size = fields.String(required=True)
    # The ssh user to use during setup
    ssh_user = fields.String(required=True)
    # The ssh public key (contents) to install on the VM
    ssh_public_key = fields.String(required=True)
    # The path to the ssh private key to use for connecting to the VM
    ssh_private_key_path = fields.String(required=True)
    # The path to the controller.yaml controller config file
    controller_config_path = fields.String(required=True)
    # The path to the storage.yaml storage backend config file
    storage_config_path = fields.String(required=True)
    # The libcloud driver name
    libcloud_provider = fields.String(required=True)
    # The inputs to the driver's constructor
    libcloud_driver_inputs = fields.Dict(keys=fields.String)
    # Additional provider-specific inputs to pass to the driver's create node method
    libcloud_create_node_inputs = fields.Dict(keys=fields.String)
    # An initialization bash script which will be run on startup. Use for things
    # like initializing credential helpers, etc.
    init_script = fields.String()

    @post_load
    def make_vm_node_config(self, data, **kwargs):
        # Look up the libcloud driver
        data["libcloud_driver"] = lookup_driver_cls(data.pop("libcloud_provider"))
        if "libcloud_driver_inputs" not in data:
            data["libcloud_driver_inputs"] = {}
        if "libcloud_create_node_inputs" not in data:
            data["libcloud_create_node_inputs"] = {}
        return VMNodeConfig(**data)


@dataclass
class K8sNodeConfig(HasDriver):
    """Configurations for a `K8sNode`"""
    
    ssh_public_key: str
    ssh_private_key_path: str
    
    def create_node_driver(self):
        pass


class K8sNodeConfigSchema(Schema):
    # The ssh public key (contents) to install on the VM
    ssh_public_key = fields.String(required=True)
    # The path to the ssh private key to use for connecting to the VM
    ssh_private_key_path = fields.String(required=True)
    
    @post_load
    def make_k8s_node_config(self, data, **kwargs):
        return K8sNodeConfig(**data)


@dataclass
class GeneralNodeConfig:
    image: str
    ports: List[int]
    cmd: str
    user_code_image: str
    httpstan_image: str
    args: Optional[List[str]] = None


class GeneralNodeConfigSchema(Schema):
    image = fields.String(required=True)
    cmd = fields.String(required=True)
    ports = fields.List(fields.Int(required=True))
    user_code_image = fields.String(required=True)
    httpstan_image = fields.String(required=True)
    args = fields.List(fields.String())

    @post_load
    def make_general_node_config(self, data, **kwargs):
        return GeneralNodeConfig(**data)


# Global registry of node config schemas
NODE_CONFIG_SCHEMAS: Dict[NodeType, Schema] = {
    NodeType.LIBCLOUD_VM: VMNodeConfigSchema(),
    NodeType.KUBERNETES_POD: K8sNodeConfigSchema()
}


@dataclass
class SchedulerConfig:
    """Configurations for the resaas scheduler

    Args:
        controller: The configurations for the control (master) node
        worker: The configurations for worker nodes
        node_type: The type of resaas node
        node_config: The corresponding configuration object for the provided
            node_type. This is used for things like generating drivers for
            connecting to the node's corresponding backend

    """

    controller: GeneralNodeConfig
    worker: GeneralNodeConfig
    node_type: NodeType
    node_config: HasDriver
    results_url_expiry_time: int
    remote_logging_config_path: str

    def create_node_driver(self):
        """Create a new node driver instance using the scheduler config"""
        return self.node_config.create_node_driver()


class SchedulerConfigSchema(Schema):
    controller = fields.Nested(GeneralNodeConfigSchema, required=True)
    worker = fields.Nested(GeneralNodeConfigSchema, required=True)
    node_type = EnumField(NodeType, by_value=True, required=True)
    remote_logging_config_path = fields.String(required=True)
    results_url_expiry_time = fields.Int()
    node_config = fields.Dict(keys=fields.String())

    @post_load
    def make_scheduler_config(self, data, **kwargs):
        # Lookup the expected schema for the driver config
        node_type = data["node_type"]
        if node_type not in NODE_CONFIG_SCHEMAS:
            raise ValidationError(f"Scheduler config specified an unknown node_type: {node_type}")
        # Parse the node_config using the matching schema
        data["node_config"] = NODE_CONFIG_SCHEMAS[node_type].load(data["node_config"])
        return SchedulerConfig(**data)


def load_scheduler_config():
    """Loads SchedulerConfig from a yaml config file

    The default path is "scheduler.yaml". To provide a custom
    config file path use the CHAINSAIL_SCHEDULER_CONFIG environment
    variable.
    """
    config_file = os.environ.get("CHAINSAIL_SCHEDULER_CONFIG", "scheduler.yaml")
    with open(config_file) as f:
        raw_config = yaml.load(f, Loader=yaml.FullLoader)
    return SchedulerConfigSchema().load(raw_config)
