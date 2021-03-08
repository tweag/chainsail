"""
A gRPC service to encapsulate the user-provided code
"""
from concurrent import futures
import logging

import click
import grpc
import numpy as np
import yaml

from resaas.common import import_from_user
from resaas.common.configs import ControllerConfigSchema
from resaas.common.logging import configure_controller_logging
from resaas.grpc import user_code_pb2_grpc, user_code_pb2


logging.basicConfig()
logger = logging.getLogger("resaas.controller")
pdf, initial_states = import_from_user()


class UserCodeServicer(user_code_pb2_grpc.UserCodeServicer):
    def LogProb(self, request, context):
        state = np.frombuffer(request.state_bytes)
        return user_code_pb2.LogProbResponse(log_prob_result=pdf.log_prob(state))

    def LogProbGradient(self, request, context):
        state = np.frombuffer(request.state_bytes)
        gradient = pdf.log_prob_gradient(state)
        return user_code_pb2.LogProbGradientResponse(gradient_bytes=gradient.tobytes())

    def InitialState(self, request, context):
        return user_code_pb2.InitialStateResponse(initial_state_bytes=initial_states.tobytes())


@click.command()
@click.option(
    "--port",
    type=int,
    default=50052,
    help="the port the gRPC server listens on",
)
@click.option(
    "--config", type=click.Path(exists=False), default=None, help="path to controller config file"
)
def run(port, config):
    # Configure logging
    if config is None:
        configure_controller_logging(
            "DEBUG",
            remote_logging=False,
            metrics_address=None,
            remote_logging_port=None,
            remote_logging_buffer_size=None,
            format_string="%(message)s",
        )
    else:
        # Load the controller configuration file
        with open(config) as f:
            config = ControllerConfigSchema().load(yaml.safe_load(f))
            # Configure logging
            configure_controller_logging(
                config.log_level,
                config.remote_logging,
                config.metrics_address,
                config.remote_logging_port,
                config.remote_logging_buffer_size,
            )

    logger.info("Starting user code gRPC server")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    user_code_pb2_grpc.add_UserCodeServicer_to_server(UserCodeServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    run()
