"""
A gRPC service to encapsulate the user-provided code
"""
import base64
from typing import Tuple
from concurrent import futures
import logging
import sys

import grpc
import numpy as np

from resaas.grpc import user_code_pb2_grpc, user_code_pb2
from resaas.common.pdfs import AbstractPDF


logging.basicConfig()
logger = logging.getLogger(__name__)


def import_from_user() -> Tuple[AbstractPDF, np.ndarray]:
    """
    Imports a user-defined pdf and corresponding initial states from
    module `probability`.
    """
    try:
        from probability import initial_states, pdf
    except ImportError as e:
        logger.exception(
            "Failed to import user-defined pdf and initial_states. Does "
            "the `probability` module exist on the PYTHONPATH? "
            f"PYTHONPATH={sys.path}"
        )
        raise e
    return (pdf, initial_states)


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


def run():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_code_pb2_grpc.add_UserCodeServicer_to_server(
        UserCodeServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()
