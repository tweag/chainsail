"""
Main entrypoint to the resaas controller
"""
from multiprocessing import Process
from typing import Tuple

import click
import yaml
from libcloud.storage.providers import get_driver
from libcloud.storage.types import Provider
from marshmallow import Schema, fields
from marshmallow.decorators import post_load
from resaas.common.storage import AbstractStorageBackend, CloudStorageBackend, LocalStorageBackend
from resaas.re_runners import MPIRERunner

from resaas.re_job_controller import LocalREJobController

ProcessStatus = Tuple[bool, str]


##############################################################################
# CONFIG
##############################################################################
def load_storage_backend(backend_name: str, backend_config: dict):
    """Loads a storage backend using the provided config.

    Args:
        backend_name: The name of the backend. See `BACKEND_SCHEMA_REGISTRY`. For
            available options.
        backend_config: The parameters required to load the specific backend. See
            the schemas in `BACKEND_SCHEMA_REGISTRY` for a list of configs.

    Raises:
        Exception: If the backend cloud not be loaded
    """
    if backend_name == "local":
        return LocalStorageBackend()
    elif backend_name == "cloud":
        try:
            provider = getattr(Provider, backend_config["provider"])
        except AttributeError:
            raise Exception(
                f"Unrecognized libcloud provider: {backend_config['provider']}. "
                "See libcloud.storage.types.Provider for a full list of available options."
            )
        driver_cls = get_driver(provider)
        driver = driver_cls(**backend_config["driver_kwargs"])
        container = driver.get_container(container_name=backend_config["container_name"])
        return CloudStorageBackend(driver, container)
    else:
        raise Exception(f"Unrecognized storage backend name: '{backend_name}'.")


class ControllerConfig:
    """Resaas controller configurations"""

    def __init__(
        self, scaler_address: str, scaler_port: int, backend_name: str, backend_config: dict
    ):
        self.scaler_address = scaler_address
        self.scaler_port = scaler_port
        self.backend_name = backend_name
        self.backend_config = backend_config

    def get_storage_backend(self) -> AbstractStorageBackend:
        """Create a new storage backend instance using the controller config"""
        return load_storage_backend(self.backend_name, self.backend_config)


##############################################################################
# CONFIG SCHEMAS
##############################################################################
class LocalBackendConfigSchema(Schema):
    # Local backend requires no config :)
    pass


class CloudBackendConfigSchema(Schema):
    libcloud_provider = fields.String(required=True)
    container_name = fields.String(required=True)
    driver_kwargs = fields.Dict(fields.String, fields.String, required=True)


BACKEND_SCHEMA_REGISTRY = {"local": LocalBackendConfigSchema, "cloud": CloudBackendConfigSchema}


class ControllerConfigSchema(Schema):
    scaler_address = fields.String(required=True)
    scaler_port = fields.Integer(required=True)
    storage_backend = fields.String(required=True)
    storage_backend_config = fields.Dict(fields.String, fields.Dict, required=True)

    @post_load
    def make_controller_config(self, data, **kwargs) -> ControllerConfig:
        # Look up the desired backend and attempt to parse its config
        try:
            schema = BACKEND_SCHEMA_REGISTRY[data["storage_backend"]]()
        except ValueError:
            # TODO: Add a controller exception type here
            raise Exception(f"Unrecognized storage_backend: '{data['storage_backend']}'")
        try:
            specified_config = data["storage_backend_config"][data["storage_backend"]]
        except ValueError:
            raise Exception(
                "Did not specify the storage_backend's corresponding config: "
                f"'{data['storage_backend']}'"
            )
        backend_config = schema.load(specified_config)
        return ControllerConfig(
            data["scaler_address"], data["scaler_port"], data["storage_backend"], backend_config
        )


##############################################################################
# ENTRYPOINT
##############################################################################


def check_status(proc: Process) -> ProcessStatus:
    # TODO: This will be called via gRPC
    pass


@click.command()
@click.argument("config_file", nargs=1, type=click.Path(exists=True))
def run(config_file):
    """
    The resaas node controller.

    Accepts a path to a YAML CONFIG_FILE.
    """
    # Load the controller configuration file
    with open(config_file) as f:
        config: ControllerConfig = ControllerConfigSchema().load(yaml.load(f))
    # Get storage backend
    backend = config.get_storage_backend()

    # TODO: Hard coded this for now
    runner = MPIRERunner
    # TODO: Need to add in the appropriate stuff to the constructor here
    controller = LocalREJobController()
    controller.run_job

    # Start controller in another process
    # Poll that process until it exits
    controller_proc = Process(target=controller.run_job, daemon=True)
    controller_proc.start()

    # TODO: Start gRPC server and bind gRPC endpoint to a function which checks whether
    #   controller_proc is still alive. If it is not alive, then
    #   we need to see if any exceptions were raised.

    # Await controller_proc, then teardown gRPC server gracefully
    controller_proc.join()


if __name__ == "__main__":
    run()
