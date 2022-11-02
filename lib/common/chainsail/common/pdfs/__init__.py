"""
Defines the interface for Chainsail-compatible PDFs.
"""
from abc import abstractmethod

import grpc
import numpy as np

from chainsail.grpc import user_code_pb2_grpc, user_code_pb2


class AbstractPDF(object):
    """Defines the interface for PDFs compatible with Chainsail."""

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
    return x.tobytes()


def _decode_array(x):
    return np.frombuffer(x)


class SafeUserPDF(AbstractPDF):
    def __init__(self, job_id, host="localhost", port=50051):
        self._channel = grpc.insecure_channel(f"{host}:{port}")
        self._stub = user_code_pb2_grpc.UserCodeStub(self.channel)
        self._job_id = job_id

    @property
    def channel(self):
        return self._channel

    @property
    def stub(self):
        return self._stub

    def log_prob(self, state):
        request = user_code_pb2.LogProbRequest(
            state_bytes=_encode_array(state), job_id=self._job_id
        )
        return self._stub.LogProb(request).log_prob_result

    def log_prob_gradient(self, state):
        request = user_code_pb2.LogProbGradientRequest(
            state_bytes=_encode_array(state), job_id=self._job_id
        )
        response = self._stub.LogProbGradient(request)
        return _decode_array(response.gradient_bytes)

    def log_likelihood(self, state):
        request = user_code_pb2.LogLikelihoodRequest(
            state_bytes=_encode_array(state), job_id=self._job_id
        )
        return self._stub.LogLikelihood(request).log_likelihood_result

    def log_likelihood_gradient(self, state):
        request = user_code_pb2.LogLikelihoodGradientRequest(
            state_bytes=_encode_array(state), job_id=self._job_id
        )
        response = self._stub.LogLikelihoodGradient(request)
        return _decode_array(response.gradient_bytes)

    def log_prior(self, state):
        request = user_code_pb2.LogPriorRequest(
            state_bytes=_encode_array(state), job_id=self._job_id
        )
        return self._stub.LogPrior(request).log_prior_result

    def log_prior_gradient(self, state):
        request = user_code_pb2.LogPriorGradientRequest(
            state_bytes=_encode_array(state), job_id=self._job_id
        )
        response = self._stub.LogPriorGradient(request)
        return _decode_array(response.gradient_bytes)
