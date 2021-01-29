"""
Main entrypoint to the resaas controller
"""
from multiprocessing import Process
from typing import Tuple

import click
import yaml
from libcloud.storage.providers import get_driver
from libcloud.storage.types import Provider
from resaas.common.runners import AbstractRERunner
from marshmallow import Schema, fields
from marshmallow.decorators import post_load
from resaas.common.storage import AbstractStorageBackend, CloudStorageBackend, LocalStorageBackend
from resaas.common.spec import JobSpecSchema
from importlib import import_module
from resaas.re_job_controller import (
    LocalREJobController,
    optimization_objects_from_spec,
    get_default_params,
)

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
            provider = getattr(Provider, backend_config["libcloud_provider"])
        except AttributeError:
            raise Exception(
                f"Unrecognized libcloud provider: {backend_config['libcloud_provider']}. "
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
        self,
        scheduler_address: str,
        scheduler_port: int,
        backend_name: str,
        backend_config: dict,
        storage_basename: str,
        runner: str,
    ):
        self.scheduler_address = scheduler_address
        self.scheduler_port = scheduler_port
        self.backend_name = backend_name
        self.backend_config = backend_config
        self.storage_basename = storage_basename
        self.runner = runner

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
    scheduler_address = fields.String(required=True)
    scheduler_port = fields.Integer(required=True)
    runner = fields.String(required=True)
    storage_backend = fields.String(required=True)
    storage_backend_config = fields.Dict(fields.String, fields.Dict, required=True)
    storage_basename = fields.String()

    @post_load
    def make_controller_config(self, data, **kwargs) -> ControllerConfig:
        # Look up the desired backend and attempt to parse its config
        try:
            schema = BACKEND_SCHEMA_REGISTRY[data["storage_backend"]]()
        except KeyError:
            # TODO: Add a controller exception type here
            raise Exception(f"Unrecognized storage_backend: '{data['storage_backend']}'")
        try:
            specified_config = data["storage_backend_config"][data["storage_backend"]]
        except KeyError:
            raise Exception(
                "Did not specify the storage_backend's corresponding config: "
                f"'{data['storage_backend']}'"
            )
        backend_config = schema.load(specified_config)
        try:
            basename = data["storage_basename"]
        except KeyError:
            basename = ""
        return ControllerConfig(
            data["scheduler_address"],
            data["scheduler_port"],
            data["storage_backend"],
            backend_config,
            basename,
            data["runner"],
        )


##############################################################################
# ENTRYPOINT
##############################################################################


def load_runner(runner_path: str) -> AbstractRERunner:
    """Loads a runner class from its module path.

    Args:
        runner: The path to the runner with the module and class delimited
            by a colon. e.g. 'some.module:MyRunner'
    """
    package, name = runner_path.split(":")
    return import_module(name, package)


def check_status(proc: Process) -> ProcessStatus:
    # TODO: This will be called via gRPC
    pass


@click.command()
@click.option("--job", required=True, type=int, help="resaas job id")
@click.option(
    "--config",
    required=True,
    type=click.Path(exists=True),
    help="path to controller YAML config file",
)
@click.option(
    "--hostsfile", required=True, type=click.Path(exists=True), help="path to job hostsfile"
)
@click.option(
    "--job-spec", required=True, type=click.Path(exists=True), help="path to job spec json file"
)
def run(job, config, hostsfile, job_spec):
    """
    The resaas node controller.
    """
    # Load the controller configuration file
    with open(config) as f:
        config: ControllerConfig = ControllerConfigSchema().load(yaml.load(f))
    # Load the job spec
    with open(job_spec) as f:
        job_spec = JobSpecSchema().loads(f.read())
    # Get storage backend
    storage_backend = config.get_storage_backend()

    # Load the controller
    runner = load_runner(config.runner)
    optimization_objects = optimization_objects_from_spec(job_spec)
    default_params = get_default_params()

    controller = LocalREJobController(
        job,
        config.scheduler_address,
        config.scheduler_port,
        *default_params,
        runner,
        storage_backend,
        basename=config.storage_basename,
        **optimization_objects,
    )

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
