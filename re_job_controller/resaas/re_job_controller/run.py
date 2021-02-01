"""
Main entrypoint to the resaas controller
"""
from dataclasses import dataclass
from importlib import import_module
from multiprocessing import Process
from typing import Tuple

import click
import yaml
from marshmallow import Schema, fields
from marshmallow.decorators import post_load
from resaas.common.runners import AbstractRERunner
from resaas.common.spec import JobSpecSchema
from resaas.common.storage import load_storage_config
from resaas.re_job_controller import (
    LocalREJobController,
    get_default_params,
    optimization_objects_from_spec,
)

ProcessStatus = Tuple[bool, str]


##############################################################################
# CONFIG
##############################################################################


@dataclass
class ControllerConfig:
    """Resaas controller configurations"""

    scheduler_address: str
    scheduler_port: int
    storage_basename: str
    runner: str


class ControllerConfigSchema(Schema):
    scheduler_address = fields.String(required=True)
    scheduler_port = fields.Integer(required=True)
    runner = fields.String(required=True)
    storage_basename = fields.String()

    @post_load
    def make_controller_config(self, data, **kwargs) -> ControllerConfig:
        return ControllerConfig(**data)


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
    "--storage",
    required=True,
    type=click.Path(exists=True),
    help="path to storage backend YAML config file",
)
@click.option(
    "--hostsfile", required=True, type=click.Path(exists=True), help="path to job hostsfile"
)
@click.option(
    "--job-spec", required=True, type=click.Path(exists=True), help="path to job spec json file"
)
def run(job, config, storage, hostsfile, job_spec):
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
    backend_config = load_storage_config(storage)
    storage_backend = backend_config.get_storage_backend()

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
