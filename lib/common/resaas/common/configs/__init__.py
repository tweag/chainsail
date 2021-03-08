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
    storage_basename: str = ""
    port: int = 50051
    n_threads: int = 10
    log_level: str = "INFO"
    remote_logging: bool = True
    remote_logging_port: int = 80
    remote_logging_buffer_size: int = 5


class ControllerConfigSchema(Schema):
    scheduler_address = fields.String(required=True)
    scheduler_port = fields.Integer(required=True)
    metrics_address = fields.String(required=True)
    metrics_port = fields.Integer(required=True)
    runner = fields.String(required=True)
    storage_basename = fields.String()
    port = fields.Integer()
    n_threads = fields.Integer()
    log_level = fields.String()
    remote_logging = fields.Boolean()
    remote_logging_port = fields.Integer()
    remote_logging_buffer_size = fields.Integer()

    @post_load
    def make_controller_config(self, data, **kwargs) -> ControllerConfig:
        return ControllerConfig(**data)
