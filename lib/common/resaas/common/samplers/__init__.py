"""
Defines the interface for RESAAS-compatible samplers.
"""
from abc import abstractmethod, abstractproperty

import numpy as np

from resaas.common.pdfs import AbstractPDF
from resaas.common.spec import LocalSampler


class AbstractSampler(object):
    """
    Defines an interface for single-chain MCMC samplers.
    """

    VARIABLE_NAME = "x"

    def __init__(self, pdf, state):
        """
        Initialize a sampler.

        Args:
          pdf(AbstractPDF): an object representing a PDF
          state(np.ndarray): an initial state
        - a string with a name for the variable this object samples from
        """
        self._pdf = pdf
        self.state = state

    @property
    def pdf(self):
        return self._pdf

    @pdf.setter
    def pdf(self, value):
        if not isinstance(value, AbstractPDF):
            raise ValueError("PDF has to be derived from AbstractPDF")
        self._pdf = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if type(value) != np.ndarray:
            raise ValueError("State has to be a NumPy array")
        self._state = value

    @abstractmethod
    def sample(self):
        """Draws a single sample."""
        pass

    @abstractproperty
    def last_draw_stats(self):
        """
        Returns a dictionary of the form
        {self.VARIABLE_NAME: SamplerStats(...)}.
        """
        pass


# this is the object occuring in the dictionary return by
# AbstractSampler.last_draw_stats. statsA,B,C (or similar) are fields
# such as acceptance rate, stepsize etc.
# SampleStats = namedtuple("SamplerStats", "statsA statsB statsC")


def get_sampler(sampler):
    """
    Looks up the sampler for a corresponding LocalSampler enum.

    Args:
      sampler: The sampler type value

    Raises:
      ValueError: If no matches were found for the specified `sampler`.
    """
    if sampler == LocalSampler.RWMC.value:
        from resaas.common.samplers.rwmc import RWMCSampler

        return RWMCSampler
    elif sampler == LocalSampler.NAIVE_HMC.value:
        from resaas.common.samplers.hmc import BasicHMCSampler

        return BasicHMCSampler
    else:
        raise ValueError(f"Unknown sampler type: {sampler}")
