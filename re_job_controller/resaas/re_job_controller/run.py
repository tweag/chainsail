"""
Main entrypoint to the resaas controller
"""
from concurrent import futures
from dataclasses import dataclass
from functools import partial
from importlib import import_module
from multiprocessing import Process
from typing import Tuple

import click
import grpc
import yaml
from marshmallow import Schema, fields
from marshmallow.decorators import post_load
from resaas.common.runners import AbstractRERunner, runner_config
from resaas.common.spec import JobSpec, JobSpecSchema
from resaas.common.storage import load_storage_config
from resaas.grpc import Health, add_HealthServicer_to_server
from resaas.re_job_controller import (
    CloudREJobController,
    optimization_objects_from_spec,
    update_nodes_mpi,
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
    runner: str
    storage_basename: str = ""
    port: int = 50051
    n_threads: int = 10


class ControllerConfigSchema(Schema):
    scheduler_address = fields.String(required=True)
    scheduler_port = fields.Integer(required=True)
    runner = fields.String(required=True)
    storage_basename = fields.String()
    port = fields.Integer()
    n_threads = fields.Integer()

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
    module, runner_name = runner_path.split(":")
    module = import_module(module)
    return getattr(module, runner_name)


def check_status(proc: Process) -> ProcessStatus:
    if proc.exitcode is None:
        return (True, "SERVING")
    elif proc.exitcode != 0:
        return (False, "FAILED")
    else:
        return (True, "SUCCESS")


@click.command()
@click.option("--job", required=True, type=str, help="resaas job id")
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
# Note: The controller is currently configured to only work with mpi, so this is not
#  abstracted away. At some point in the future the hostsfile logic could get moved
#  into its own area. The main thing is that with a master-worker achitecture, the
#  master process (running the controller in the current case) needs a way of identifying
#  the workers.
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
        config: ControllerConfig = ControllerConfigSchema().load(yaml.safe_load(f))
    # Load the job spec
    with open(job_spec) as f:
        job_spec: JobSpec = JobSpecSchema().loads(f.read())
    # Get storage backend
    backend_config = load_storage_config(storage)
    storage_backend = backend_config.get_storage_backend()

    # Load the controller
    runner = load_runner(config.runner)()
    # TODO: Hard-coding this for now until we have a need for multiple runners
    runner_config["hostsfile"] = hostsfile
    runner_config["run_id"] = job
    runner_config["storage_config"] = storage

    optimization_objects = optimization_objects_from_spec(job_spec)

    controller = CloudREJobController(
        job,
        config.scheduler_address,
        config.scheduler_port,
        job_spec.replica_exchange_parameters,
        job_spec.local_sampling_parameters,
        job_spec.optimization_parameters,
        runner,
        storage_backend,
        node_updater=partial(update_nodes_mpi, hostsfile),
        basename=config.storage_basename,
        **optimization_objects,
    )

    # Start controller in another process
    controller_proc = Process(target=controller.run_job, daemon=True)
    controller_proc.start()

    # Gets the status of the controller process
    def controller_state():
        return check_status(controller_proc)[1]

    # Start gRPC server
    with futures.ThreadPoolExecutor(max_workers=config.n_threads) as ex:
        server = grpc.server(ex)
        add_HealthServicer_to_server(Health(callback=controller_state), server)
        server.add_insecure_port(f"[::]:{config.port}")
        server.start()
        server.wait_for_termination()


if __name__ == "__main__":
    run()
