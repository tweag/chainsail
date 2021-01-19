"""
Scheduler app configuration file parsing
"""
import os
from typing import Callable, Dict, List, Optional, Tuple

from libcloud.compute.drivers.ec2 import EC2NodeDriver
from libcloud.compute.drivers.gce import GCENodeDriver
from marshmallow import Schema, fields
from marshmallow.decorators import post_load
from marshmallow.exceptions import ValidationError
from marshmallow_enum import EnumField
import yaml

from resaas.scheduler.nodes.base import NodeType
from resaas.scheduler.nodes.mock import DeployableDummyNodeDriver


class GCEDriverConfigSchema(Schema):
    user_id = fields.String(required=True)
    key = fields.String(required=True)
    project = fields.String(required=True)
    datacenter = fields.String(required=True)
    extra_creation_args = fields.Dict(fields.String(), fields.String())


class EC2DriverConfigSchema(Schema):
    class EC2ExtraArgs(Schema):
        ex_security_groups = fields.List(fields.String)

    key = fields.String(required=True)
    secret = fields.String(required=True)
    token = fields.String(required=True)
    region = fields.String(required=True)
    extra_creation_args = fields.Nested(EC2ExtraArgs, required=True)


class DummyDriverConfigSchema(Schema):
    creds = fields.String(required=True)
    extra_creation_args = fields.Dict(fields.String, fields.String)


DRIVER_SCHEMAS: Dict[NodeType, Dict[str, Tuple[Callable, Schema]]] = {
    NodeType.LIBCLOUD_VM: {
        "gce": (GCENodeDriver, GCEDriverConfigSchema),
        "dummy": (DeployableDummyNodeDriver, DummyDriverConfigSchema),
        "ec2": (EC2NodeDriver, EC2DriverConfigSchema),
    }
}


class SchedulerConfig:
    def __init__(
        self,
        ssh_user: str,
        ssh_public_key: str,
        ssh_private_key_path: str,
        node_entrypoint: str,
        node_ports: Optional[List[int]],
        node_image: str,
        node_size: str,
        node_type: NodeType,
        driver: Callable,
        driver_kwargs: Dict,
        extra_creation_kwargs: Optional[Dict],
        # driver_args is currently unused
        driver_args: Tuple = (),
    ):
        self.ssh_user = ssh_user
        self.ssh_public_key = ssh_public_key
        self.ssh_private_key_path = ssh_private_key_path
        self.node_entrypoint = node_entrypoint
        if node_ports is None:
            self.node_ports = []
        else:
            self.node_ports = node_ports
        self.image = node_image
        self.size = node_size
        self.node_type = node_type
        self.driver = driver
        self.driver_args = driver_args
        self.driver_kwargs = driver_kwargs
        if extra_creation_kwargs is None:
            self.extra_creation_kwargs = {}
        else:
            self.extra_creation_kwargs = extra_creation_kwargs

    def create_node_driver(self):
        """Create a new node driver instance using the scheduler config"""
        return self.driver(*self.driver_args, **self.driver_kwargs)


class SchedulerConfigSchema(Schema):
    """Schema for parsing scheduler configuration files.

    To aid in prototyping, this schema works by allowing users to specify a
    driver id which must exist in the 'DRIVER_SCHEMAS' global registry. Required
    arguments for instantiating the various drivers are declared in this registry
    using a separate schema for each driver type. See GCEDriverConfigSchema
    for an example.
    """

    ssh_user = fields.String(required=True)
    ssh_public_key = fields.String(required=True)
    ssh_private_key_path = fields.String(required=True)
    node_entrypoint = fields.String(required=True)
    node_ports = fields.List(fields.Integer, required=True)
    node_image = fields.String(required=True)
    node_size = fields.String(required=True)
    # The type of nodes to instantiate
    node_type = EnumField(NodeType, by_value=True, required=True)
    node_driver = fields.String(required=True)
    # Initial parsing converts driver info into a dict. We will
    # then verify that all of the expected fields exist in that dict.
    driver_specs = fields.Dict(fields.String, fields.Dict)

    @post_load
    def make_scheduler_config(self, data, **kwargs):
        # Lookup the expected schema for the driver config
        node_type = data["node_type"]
        if node_type not in DRIVER_SCHEMAS:
            raise ValidationError(f"Scheduler config specified an unknown node_type: {node_type}")
        requested_driver = data["node_driver"]
        if requested_driver not in DRIVER_SCHEMAS[node_type]:
            raise ValidationError(
                f"Scheduler config specified an unknown driver type: {requested_driver}"
            )
        driver, driver_config_schema = DRIVER_SCHEMAS[node_type][requested_driver]
        if requested_driver not in data["driver_specs"]:
            raise ValidationError(
                f"Scheduler config specified node_driver '{requested_driver}' but did not "
                "specify corresponding specs for it in driver_specs."
            )
        # Validate that the required config fields exist
        driver_config = driver_config_schema().load(data["driver_specs"][requested_driver])
        if "extra_creation_kargs" not in driver_config:
            extra_creation_kwargs = {}
        else:
            extra_creation_kwargs = driver_config.pop("extra_creation_kargs")
        return SchedulerConfig(
            ssh_user=data["ssh_user"],
            ssh_public_key=data["ssh_public_key"],
            ssh_private_key_path=data["ssh_private_key_path"],
            node_entrypoint=data["node_entrypoint"],
            node_ports=data["node_ports"],
            node_image=data["node_image"],
            node_size=data["node_size"],
            node_type=data["node_type"],
            driver=driver,
            driver_args=(),
            driver_kwargs=driver_config,
            extra_creation_kwargs=extra_creation_kwargs,
        )


def load_scheduler_config():
    """Loads SchedulerConfig from a yaml config file

    The default path is "scheduler.yaml". To provide a custom
    config file path use the RESAAS_SCHEDULER_CONFIG environment
    variable.
    """
    config_file = os.environ.get("RESAAS_SCHEDULER_CONFIG", "scheduler.yaml")
    with open(config_file) as f:
        raw_config = yaml.load(f, Loader=yaml.FullLoader)
    return SchedulerConfigSchema().load(raw_config)
