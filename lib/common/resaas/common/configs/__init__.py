"""
Configuration file schemata
"""
from dataclasses import dataclass

from marshmallow import Schema, fields
from marshmallow.decorators import post_load


@dataclass
class ControllerConfig:
    """Resaas controller configurations"""

    scheduler_address: str
    scheduler_port: int
    metrics_address: str
    metrics_port: int
    runner: str
    remote_logging_config_path: str
    storage_basename: str = ""
    port: int = 50051
    n_threads: int = 10
    log_level: str = "INFO"


class ControllerConfigSchema(Schema):
    scheduler_address = fields.String(required=True)
    scheduler_port = fields.Integer(required=True)
    metrics_address = fields.String(required=True)
    metrics_port = fields.Integer(required=True)
    runner = fields.String(required=True)
    remote_logging_config_path = fields.String(required=True)
    storage_basename = fields.String()
    port = fields.Integer()
    n_threads = fields.Integer()
    log_level = fields.String()

    @post_load
    def make_controller_config(self, data, **kwargs) -> ControllerConfig:
        return ControllerConfig(**data)


@dataclass
class RemoteLoggingConfig:
    """Gaphite logging configurations"""

    address: str
    enabled: bool
    log_level: str = "INFO"
    port: int = 80
    buffer_size: int = 5
    format_string: str = "[%(levelname)s] %(asctime)s - %(message)s"


class RemoteLoggingConfigSchema(Schema):
    enabled = fields.Boolean(required=True)
    address = fields.String(required=True)
    log_level = fields.String()
    port = fields.Integer()
    buffer_size = fields.Integer()
    format_string = fields.String()

    @post_load
    def make_remote_logging_config(self, data, **kwargs) -> RemoteLoggingConfig:
        return RemoteLoggingConfig(**data)
