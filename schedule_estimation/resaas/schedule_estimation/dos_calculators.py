"""
Classes which estimate the density of states (DOS) from MCMC samples from a
distribution at different "temperatures".
"""
import numpy as np
from abc import abstractmethod, ABCMeta

from util import log_sum_exp


def log(text):
    """Write a log entry.
    
    TODO: we might log to some database or a file instead of stdout

    Args:
      text: 

    Returns:

    """
    # print(text)
    pass


class AbstractWHAM(metaclass=ABCMeta):
    def __init__(self, energies, log_ensemble, parameters):
        """Interface for classes implementing WHAM

        Args:
          energies(:class:`np.ndarray`): negative log-probabilities
              ("energies") of states in their respective ensembles
          log_ensemble(callable): function taking a single sample and a 
              dictionary of parameterslogarithm of the probability density
              defining the ensemble
          parameters(dict): Parameter values defining the ensemble at different
              "temperatures". The keys are the parameter names and the values
              :class:`np.ndarray`s with the parameter values corresponding to
              the first dimension of the ``energies`` argument
        """
        self.energies = energies
        self.log_ensemble = log_ensemble
        self.parameters = parameters
        self.n_ensembles = energies.shape[0]

    def validate_shapes(self, energies, parameters):
        """
        Makes sure that energies and replica parameter shapes make sense and
        match.

        Args:
          energies(:class:`np.ndarray`): negative log-probabilities
              ("energies") of states in their respective ensembles
          parameters(dict): Parameter values defining the ensemble at different
              "temperatures". The keys are the parameter names and the values
              :class:`np.ndarray`s with the parameter values corresponding to
              the first dimension of the ``energies`` argument
        """
        param_shapes = {}
        for key, val in parameters.items():
            if val.shape[0] == 0:
                raise ValueError(('Parameter arrays need to have at least '
                                  'length 1'))
            param_shapes[key] = val.shape[0]
        if not len(set(param_shapes)) == 1:
            raise ValueError('Parameter array shapes are not equal')
        param_shape = val.shape[0]
        if energies.shape[0] != param_shape:
            raise ValueError(('First dimension of energies array needs to be '
                              'of same length as parameter arrays'))
    
    @abstractmethod
    def run(self, n_iterations=5000):
        """
        Runs WHAM iterations.

        Args:
          n_iterations(int):  number of WHAM iterations to run.
              (Default value = 5000)

        Returns:
          :class:`np.ndarray`: estimates of the log-density of states at the
              sampled energies
        """
        pass


class DefaultWHAM(AbstractWHAM):
    def calculate_log_qs(self):
        """Builds up the matrix of the log-probabilities of the energies in all
        ensembles.

        Returns:
          :class:`np.ndarray`: matrix of the log-probabilities of all energies
              in all ensembles.
        """
        param_dicts = [{param: self.parameters[param][i] for param in
                        self.parameters} for i in range(self.n_ensembles)]
        log_qs = np.array([self.log_ensemble(self.energies.ravel(), **params)
                           for params in param_dicts])

        return log_qs

    def stopping_criterion(self, log_L, previous_log_L, termination_threshold):
        """
        Defines a convergence criterion for stopping the WHAM iteration.

        Args:
          log_L(float): log-likelihood given the current DOS estimate
          previous_log_L(float): log-likelihood given the previous DOS estimate
          termination_threshold(float): relative difference between old and new
              likelihoods which defines convergence

        Returns:
          bool: whether WHAM iteration has converged or not
        """
        return abs(log_L - previous_log_L) / log_L < termination_threshold

    def calc_log_L(self, f, log_g):
        """
        Calculates the log-likelihood of the energies for values of the free
        energies and the log-DOS.

        Args:
          f(:class:`np.ndarray`): estimate of the free energies of the
              ensembles
          log_g: estimate of the log-DOS evaluated at the sampled energies

        Returns:
          float: estimate of the log-likelihhod of the energies
        """
        return -f.sum() + log_g.sum()

    def run(self, max_iterations=5000, threshold=1e-6):
        """Do multiple histogram reweighting with infinitely fine binning as
        outlined in the paper "Evaluation of marginal likelihoods via the
        density of states" (Habeck, AISTATS 2012)

        Args:
          max_iterations: how many WHAM iterations to perform.
              (Default value = 5000)
          threshold(float): log-likelihood difference threshold surpassing
              of which means the iteration converged. (Default value = 1e-6)

        Returns:
          :class:`np.ndarray`: estimate of the log-DOS evaluated at the sampled
              energies
        """
        f = np.zeros(self.n_ensembles)
        log_qs = self.calculate_log_qs()

        old_log_L = 1e300
        for i in range(max_iterations):
            log_gs = -log_sum_exp(log_qs + f[:, None], axis=0)
            log_gs -= log_sum_exp(log_gs)
            f = -log_sum_exp((log_qs + log_gs).T, axis=0)

            log_L = self.calc_log_L(f, log_gs)
            if i % 1 == 0:
                log('Likelihood: {}'.format(log_L))
            # if self.stopping_criterion(log_L, old_log_L, threshold):
            #     break
            old_log_L = log_L
                
        if i > 0.8 * max_iterations:
            log(('More than 80% of max WHAM iterations were required. '
                 'Histogram reweighting might not have converged.'))

        return log_gs


class AbstractDOSCalculator(metaclass=ABCMeta):
    def __init__(self, wham_class=DefaultWHAM, max_wham_iterations=5000,
                 wham_threshold=1e-6):
        '''
        Defines the interface for classes which estimate the density
        of states (DOS) for different families of tempered distributions
        ("ensembles").
        '''
        self.wham_class = wham_class
        self.max_wham_iterations = max_wham_iterations
        self.wham_threshold = wham_threshold

    @abstractmethod
    def log_ensemble(self, energy, **parameters):
        """An ensemble is essentially a function q(E) which maps an energy
        E to a probability q. It might be parameterized.

        Args:
          energy(float): energy of the system
          **parameters(dict): dictionary of ensemble parameters

        Returns:
          float: the log-probability of the energy in the ensemble specified
              by the parameters.
        """
        pass

    def calculate_dos(self, energies, parameters):
        """Calculate the density of states (DOS) using multiple histogram
        reweighting (WHAM).

        Args:
          energies(:class:`np.ndarray`): negative log-probabilities
              ("energies") of states in their respective ensembles. Shape:
              (# ensembles, # samples per ensemble)
          parameters(dict): parameter values defining the ensemble at different
              "temperatures" Keys are the parameter names and the values 
              :class:`np.ndarray`s with the parameter values corresponding
              to the first dimension of the ``energies`` argument

        Returns:
          :class:`np.ndarray`: estimate of the log-DOS evaluated at the sampled
              energies
        """
        wham = self.wham_class(energies, self.log_ensemble, parameters)
        log_dos = wham.run(self.max_wham_iterations, self.wham_threshold)

        return log_dos


class BoltzmannDOSCalculator(AbstractDOSCalculator):
    def log_ensemble(self, energy, beta):
        """Implements the Boltzmann ensemble q(E|\beta) = exp(-beta * E)

        Args:
          energy(float): energy of the system
          beta(float): inverse temperature

        Returns:
          float: probability of the given energy in a Boltzmann ensemble at
              inverse temperature beta
        """
        return -beta * energy
