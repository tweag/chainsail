"""
Main entrypoint to the Chainsail controller
"""
import logging
from concurrent import futures
from functools import partial
from importlib import import_module
from multiprocessing import Process
from typing import Tuple

import click
import grpc
import yaml
from chainsail.common.configs import ControllerConfig, ControllerConfigSchema
from chainsail.common.custom_logging import configure_logging
from chainsail.common.runners import AbstractRERunner, runner_config
from chainsail.common.spec import JobSpec, JobSpecSchema
from chainsail.common.storage import load_storage_config
from chainsail.controller import (
    CloudREJobController,
    optimization_objects_from_spec,
    update_nodes_mpi,
)
from chainsail.grpc import Health, add_HealthServicer_to_server
from chainsail.grpc import user_code_pb2_grpc, user_code_pb2

ProcessStatus = Tuple[bool, str]


logger = logging.getLogger("chainsail.controller")
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
    logger.debug(f"Attempting to load runner '{runner_name}' from {module}")
    module = import_module(module)
    return getattr(module, runner_name)


def check_status(proc: Process) -> ProcessStatus:
    if proc.exitcode is None:
        return (True, "SERVING")
    elif proc.exitcode != 0:
        return (False, "FAILED")
    else:
        return (True, "SUCCESS")


def check_user_code_server_ready(host="localhost", port=50052, timeout=1.0):
    """
    Check if the user code server is ready to handle requests within the timeout.

    Args:
        host: Hostname of the user code server
        port: Port of the user code server
        timeout: Timeout in seconds for the health check

    Returns:
        bool: True if user code server is ready, False otherwise
    """
    try:
        # Create a channel with timeout
        channel = grpc.insecure_channel(f"{host}:{port}")

        # Use the channel with a timeout for the call
        stub = user_code_pb2_grpc.HealthStub(channel)
        request = user_code_pb2.HealthCheckRequest(service="")

        # Make the health check call with timeout
        response = stub.Check(request, timeout=timeout)

        # Check if the response indicates the server is serving
        is_ready = response.status == user_code_pb2.HealthCheckResponse.SERVING

        # Close the channel
        channel.close()

        logger.debug(
            f"User code server health check: status={response.status}, ready={is_ready}"
        )
        return is_ready

    except grpc.RpcError as e:
        logger.debug(
            f"User code server health check failed with gRPC error: "
            f"{e.code()} - {e.details()}"
        )
        return False
    except Exception as e:
        logger.debug(f"User code server health check failed with error: {e}")
        return False


@click.command()
@click.option("--job", required=True, type=str, help="Chainsail job id")
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
#  abstracted away. At some point in the future the hostfile logic could get moved
#  into its own area. The main thing is that with a master-worker achitecture, the
#  master process (running the controller in the current case) needs a way of identifying
#  the workers.
@click.option(
    "--hostfile", required=True, type=click.Path(exists=False), help="path to job hostfile"
)
@click.option(
    "--job-spec", required=True, type=click.Path(exists=True), help="path to job spec json file"
)
def run(job, config, storage, hostfile, job_spec):
    """
    The Chainsail node controller.
    """
    # Load the controller configuration file
    with open(config) as f:
        config: ControllerConfig = ControllerConfigSchema().load(yaml.safe_load(f))
    configure_logging(
        "chainsail.controller", config.log_level, config.remote_logging_config_path, job_id=job
    )

    logger.debug("Loading job spec from file")
    with open(job_spec) as f:
        job_spec: JobSpec = JobSpecSchema().loads(f.read())

    logger.debug("Loading storage config file")
    backend_config = load_storage_config(storage)
    logger.debug("Initializing storage backend using config")
    storage_backend = backend_config.get_storage_backend()

    # Load the controller
    runner = load_runner(config.runner)()
    # TODO: Hard-coding this for now until we have a need for multiple runners
    runner_config["hostfile"] = hostfile
    runner_config["run_id"] = job
    runner_config["storage_config"] = storage
    runner_config["metrics_host"] = config.metrics_address
    runner_config["metrics_port"] = config.metrics_port

    logger.debug(repr(runner_config))

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
        tempered_dist_family=job_spec.tempered_dist_family,
        node_updater=partial(update_nodes_mpi, hostfile_path=hostfile),
        dirname=f"{config.storage_dirname}/{job}",
        **optimization_objects,
    )

    # Start controller in another process
    def wrapped_run_job():
        try:
            controller.run_job()
        except Exception as e:
            # Ensures that top-level errors in the controller get logged
            logger.exception(e)
            raise e

    controller_proc = Process(target=wrapped_run_job, daemon=True)
    controller_proc.start()

    # Gets the status of the controller process
    def controller_state():
        # First check if the controller process itself is running
        process_ready, process_status = check_status(controller_proc)

        if not process_ready:
            logger.debug(f"Controller process not ready: {process_status}")
            return process_status

        # If controller process is running, check if user code server is ready
        user_code_ready = check_user_code_server_ready()

        if not user_code_ready:
            logger.debug("User code server not ready, controller reporting NOT_SERVING")
            return "NOT_SERVING"

        logger.debug("Both controller process and user code server are ready")
        return process_status

    # Start gRPC server
    with futures.ThreadPoolExecutor(max_workers=config.n_threads) as ex:
        server = grpc.server(ex)
        add_HealthServicer_to_server(Health(callback=controller_state), server)
        server.add_insecure_port(f"[::]:{config.port}")
        server.start()
        server.wait_for_termination()


if __name__ == "__main__":
    run()
