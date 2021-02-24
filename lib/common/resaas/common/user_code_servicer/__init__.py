"""
A gRPC service to encapsulate the user-provided code
"""
import base64
from typing import Tuple

import numpy as np

from resaas.common.user_code_servicer import user_code_pb2_grpc
from resaas.common.pdfs import AbstractPDF


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
        state = base64.b64decode(request.b64state)
        return pdf.log_prob(state)

    def LogProbGradient(self, request, context):
        state = base64.b64decode(request.b64state)
        gradient = pdf.log_prob_gradient(state)
        return base64.b64encode(gradient)

    def InitialState(self, request, context):
        return base64.b64encode(initial_states)
