"""
A gRPC service to encapsulate the user-provided code
"""
from concurrent import futures
import logging

import click
import grpc
import numpy as np

from resaas.common import import_from_user
from resaas.common.custom_logging import configure_logging
from resaas.grpc import user_code_pb2_grpc, user_code_pb2


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
        logger.info("Retrieving initial state", extra={"job_id": request.job_id})
        return user_code_pb2.InitialStateResponse(initial_state_bytes=initial_states.tobytes())


@click.command()
@click.option(
    "--port",
    type=int,
    default=50052,
    help="the port the gRPC server listens on",
)
@click.option(
    "--remote_logging_config", type=click.Path(exists=False), default=None, help="path to remote logging config file"
)
def run(port, remote_logging_config):
    # Configure logging
    configure_logging("resaas.controller",
                      "INFO",
                      remote_logging_config
    )

    logger.debug("Starting user code gRPC server")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    user_code_pb2_grpc.add_UserCodeServicer_to_server(UserCodeServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    run()
