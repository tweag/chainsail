"""
Various statistical ensembles.

A statistical ensemble is a non-negative, potentially parameterized function
mapping an energy to real number.
"""
from abc import ABC, abstractmethod


class Ensemble(ABC):
    """
    Interface for classes implementing statistical ensembles.

    An ensemble is essentially a function q(E) which maps an energy
    E to a probability q. It might be parameterized.
    """

    @staticmethod
    @abstractmethod
    def log_ensemble(energy, **parameters):
        """Log-probability of an energy in this ensemble at given
        ensemble parameters.

        Args:
          energy(float): energy of the system
          **parameters(dict): dictionary of ensemble parameters

        Returns:
          float: the log-probability of the energy in the ensemble specified
              by the parameters.
        """
        pass

    @staticmethod
    @abstractmethod
    def log_ensemble_derivative(energy, **parameters):
        """Derivative of the log-probability of an energy in this ensemble at
        w.r.t. given ensemble parameters.

        Args:
          energy(float): energy of the system
          **parameters(dict): dictionary of ensemble parameters

        Returns:
          float: the derivative of the log-probability of the energy in the
              ensemble specified by the parameters.
        """
        pass


class BoltzmannEnsemble(Ensemble):
    @staticmethod
    def log_ensemble(energy, beta):
        """Implements the Boltzmann ensemble q(E|\beta) = exp(-beta * E).

        Args:
          energy(float): energy of the system
          beta(float): inverse temperature

        Returns:
          float: probability of the given energy in a Boltzmann ensemble at
              inverse temperature beta
        """
        return -beta * energy

    @staticmethod
    def log_ensemble_derivative(energy, beta):
        """Implements the gradient of the Boltzmann ensemble.

        Args:
          energy(float): energy of the system
          beta(float): inverse temperature

        Returns:
          float: derivative of the log-probability of the energy in a Boltzmann
              ensemble at inverse temperature beta
        """
        return -beta
