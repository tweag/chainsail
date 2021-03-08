"""
Main entrypoint to the resaas controller
"""
import logging
import os
from multiprocessing import Process
from tempfile import TemporaryDirectory
from typing import Tuple

import click
import yaml
from resaas.common.logging import configure_controller_logging
from resaas.common.runners import runner_config
from resaas.common.spec import (
    JobSpec,
    JobSpecSchema,
)
from resaas.common.storage import LocalStorageBackend
from resaas.controller import BaseREJobController, optimization_objects_from_spec
from resaas.runners.rexfw import MPIRERunner

ProcessStatus = Tuple[bool, str]

logger = logging.getLogger("resaas.controller")
##############################################################################
# ENTRYPOINT
##############################################################################


def check_status(proc: Process) -> ProcessStatus:
    # TODO: This will be called via gRPC
    pass


@click.command()
@click.option(
    "--basename", required=True, type=click.Path(), help="basename for simulation output"
)
@click.option(
    "--job-spec", required=True, type=click.Path(exists=True), help="path to job spec json file"
)
def run(basename, job_spec):
    """
    The resaas node controller.
    """
    # Configure logging
    configure_controller_logging(
        "DEBUG",
        # remote_logging=False,
        # metrics_address=None,
        # remote_logging_port=None,
        # remote_logging_buffer_size=None,
        remote_logging=True,
        metrics_address="localhost",
        remote_logging_port=8080,
        remote_logging_buffer_size=5,
        format_string="%(message)s",
    )

    # Load the job spec
    with open(job_spec) as f:
        job_spec: JobSpec = JobSpecSchema().loads(f.read())
    storage_backend = LocalStorageBackend()

    # Load the controller
    runner = MPIRERunner()
    # TODO: Hard-coding this for now until we have a need for multiple runners
    tempdir = TemporaryDirectory()
    hostsfile = os.path.join(tempdir.name, "hostsfile")
    with open(hostsfile, "w") as f:
        for _ in range(job_spec.max_replicas):
            f.write("localhost\n")
    storage = os.path.join(tempdir.name, "storage.yaml")
    with open(storage, "w") as f:
        yaml.dump({"backend": "local", "backend_config": {"local": {}}}, f)

    runner_config["hostsfile"] = hostsfile
    runner_config["run_id"] = "loocal"
    runner_config["storage_config"] = storage
    runner_config["storage_config"] = storage

    optimization_objects = optimization_objects_from_spec(job_spec)

    controller = BaseREJobController(
        job_spec.replica_exchange_parameters,
        job_spec.local_sampling_parameters,
        job_spec.optimization_parameters,
        runner,
        storage_backend,
        basename=basename,
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

    tempdir.cleanup()


if __name__ == "__main__":
    run()
