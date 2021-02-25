"""
Defines the interface for RESAAS-compatible PDFs.
"""
from abc import abstractmethod
import base64

import grpc
import numpy as np

from resaas.grpc import user_code_pb2_grpc, user_code_pb2


class AbstractPDF(object):
    """Defines the interface for PDFs compatible with RESAAS."""

    @abstractmethod
    def log_prob(self, x):
        """
        Log-probability of the probablity density.

        Args:
          x(np.ndarray): variates of the probability density
        """
        pass

    @abstractmethod
    def log_prob_gradient(self, x):
        """
        Gradient of the densities' log-probability.

        Args:
          x(np.ndarray): variates of the probability density
        """
        pass


def _encode_array(x):
    return base64.b64encode(x)


def _decode_array(x):
    return base64.b64decode(x)


class SafeUserPDF(AbstractPDF):
    def __init__(self, host="localhost", port=50051):
        channel = grpc.insecure_channel(f"{host}:{port}")
        self._stub = user_code_pb2_grpc.UserCodeStub(channel)

    def log_prob(self, state):
        request = user_code_pb2.LogProbRequest(b64state=_encode_array(state))
        return self._stub.LogProb(request).log_prob_result

    def log_prob_gradient(self, state):
        request = user_code_pb2.LogProbGradientRequest(b64state=_encode_array(state))
        response = self._stub.LogProbGradient(request)
        return np.frombuffer(_decode_array(response.b64gradient_result), dtype=float)
