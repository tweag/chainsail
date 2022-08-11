"""
Main entrypoint to the resaas controller
"""
import os
from multiprocessing import Process
from tempfile import TemporaryDirectory
from typing import Tuple

import click
import yaml
from chainsail.common.custom_logging import configure_logging
from chainsail.common.runners import runner_config
from chainsail.common.spec import (
    JobSpec,
    JobSpecSchema,
)
from chainsail.common.storage import LocalStorageBackend
from chainsail.controller import BaseREJobController, optimization_objects_from_spec
from chainsail.runners.rexfw import MPIRERunner

ProcessStatus = Tuple[bool, str]

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
@click.option(
    "--remote-logging-config-path",
    default=None,
    type=click.Path(),
    help="Config file with remote logging settings",
)
def run(basename, job_spec, remote_logging_config_path):
    """
    The resaas node controller.
    """
    # Configure logging
    configure_logging(
        "chainsail.controller",
        "DEBUG",
        remote_logging_config_path=remote_logging_config_path,
        format_string="%(message)s",
        job_id=-1,
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
    runner_config["run_id"] = -1
    runner_config["storage_config"] = storage
    runner_config["storage_config"] = storage

    optimization_objects = optimization_objects_from_spec(job_spec)

    controller = BaseREJobController(
        job_spec.replica_exchange_parameters,
        job_spec.local_sampling_parameters,
        job_spec.optimization_parameters,
        runner,
        storage_backend,
        job_spec.tempered_dist_family, 
        basename=basename,
        **optimization_objects,                                                                               #changed
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
