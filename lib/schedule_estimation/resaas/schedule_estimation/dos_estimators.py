"""
Classes which estimate the density of states (DOS) from MCMC samples from a
distribution at different "temperatures".
"""
import logging

import numpy as np
from resaas.common.util import log_sum_exp

logger = logging.getLogger(__name__)


def stopping_criterion(log_L, previous_log_L, stopping_threshold):
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
    return abs((log_L - previous_log_L) / (log_L + previous_log_L)) < stopping_threshold


def validate_shapes(energies, parameters):
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
            raise ValueError(("Parameter arrays need to have at least " "length 1"))
        param_shapes[key] = val.shape[0]
    if not len(set(param_shapes)) == 1:
        raise ValueError("Parameter array shapes are not equal")
    param_shape = val.shape[0]
    if energies.shape[0] != param_shape:
        raise ValueError(
            ("First dimension of energies array needs to be " "of same length as parameter arrays")
        )


def calculate_log_L(f, log_g):
    """
    Calculates the log-likelihood of the energies for values of the free
    energies and the log-DOS.

    Args:
      f(:class:`np.ndarray`): estimate of the free energies of the
          ensembles
      log_g: estimate of the log-DOS evaluated at the sampled energies

    Returns:
      float: estimate of the log-likelihood of the energies
    """
    return -f.sum() + log_g.sum()


class WHAM:
    def __init__(self, ensemble):
        """Initializes an WHAM object.

        This requires the sampled energies, a function describing the
        log-ensemble and a dictionary of ensemble parameters which describe
        the ensemble instances from which the energies were sampled.
        The underlying algorithm is described in Michael Habeck's \"Evaluation
        of marginal likelihoods via the density of states.\", AISTATS (2012).

        Args:
          ensemble(:class:`Ensemble): the ensemble from which the energies
              were sampled
        """
        self._ensemble = ensemble

    def _calculate_log_qs(self, energies, parameters):
        """Builds up the matrix of the log-probabilities of the energies in all
        ensembles.

        Args:
            energies(:class:`np.ndarray`): negative log-probabilities
              ("energies") of states in their respective ensembles
            parameters(dict): Parameter values defining the ensemble at different
              "temperatures". The keys are the parameter names and the values
              :class:`np.ndarray`s with the parameter values corresponding to
              the first dimension of the ``energies`` argument

        Returns:
          :class:`np.ndarray`: matrix of the log-probabilities of all energies
              in all ensembles.
        """
        n_ensembles = energies.shape[0]
        param_dicts = [
            {param: parameters[param][i] for param in parameters} for i in range(n_ensembles)
        ]
        log_qs = np.array(
            [self._ensemble.log_ensemble(energies.ravel(), **params) for params in param_dicts]
        )

        return log_qs

    def estimate_dos(self, energies, parameters, max_iterations=5000, stopping_threshold=1e-10):
        """Do multiple histogram reweighting with infinitely fine binning as
        outlined in the paper "Evaluation of marginal likelihoods via the
        density of states" (Habeck, AISTATS 2012)

        Args:
            energies(:class:`np.ndarray`): negative log-probabilities
              ("energies") of states in their respective ensembles
            parameters(dict): Parameter values defining the ensemble at different
              "temperatures". The keys are the parameter names and the values
              :class:`np.ndarray`s with the parameter values corresponding to
              the first dimension of the ``energies`` argument
            max_iterations(int): maximum number of WHAM iterations to perform
              stopping_threshold(float): relative difference in log-likelihoods
              of energies which measures convergence of WHAM iterations.

        Returns:
            :class:`np.array`: an estimate of the DOS at the sampled energies
        """
        validate_shapes(energies, parameters)
        f = np.zeros(energies.shape[0])
        log_qs = self._calculate_log_qs(energies, parameters)

        old_log_L = 1e300
        for i in range(max_iterations):
            log_gs = -log_sum_exp(log_qs + f[:, None], axis=0)
            log_gs -= log_sum_exp(log_gs)
            f = -log_sum_exp((log_qs + log_gs).T, axis=0)

            log_L = calculate_log_L(f, log_gs)
            if i % 10 == 0:
                logger.info("Likelihood of energies given DOS: {}".format(log_L))
            if stopping_criterion(log_L, old_log_L, stopping_threshold):
                break
            old_log_L = log_L

        if i > 0.8 * max_iterations:
            logger.warning(
                (
                    "More than 80% of max WHAM iterations were required. "
                    "Histogram reweighting might not have converged."
                )
            )

        return log_gs
