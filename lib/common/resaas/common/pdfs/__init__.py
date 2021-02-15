"""
Defines the interface for RESAAS-compatible PDFs.
"""

from abc import abstractmethod


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
