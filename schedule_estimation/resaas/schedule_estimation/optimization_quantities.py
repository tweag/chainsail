"""
Logic which calculates quantities such as acceptance rates and normalization
constants from an estimate of the density of states (DOS) and the energies it
was calculated from.
"""
from typing import Callable

import numpy as np
from resaas.common.spec import OptimizationQuantity
from resaas.common.util import log_sum_exp


def log_partition_function(dos, energies, beta):
    """
    Calculates an estimate of the log partition function at a given
    inverse temperature.

    Uses the DOS estimate and sampled energies to calculate an estimate of the
    partition function Z(beta) at a given inverse temperature ``beta``.

    Args:
        dos(:class:`np.ndarray): estimate of density of states (DOS) evaluated
          at sampled energies
        energies(:class:`np.ndarray): sampled energies
        beta(float): inverse temperature
    """
    return log_sum_exp((-energies.ravel() * beta + dos).T, axis=0)


def acceptance_rate(dos, energies, beta1, beta2):
    """
    Estimates acceptance rate between two neighboring replicas.

    Uses the DOS estimate and sampled energies to calculate the expected
    acceptance rate between two replicas in a Boltzmann schedule with inverse
    temperatures ``beta1`` and ``beta2``.

    Args:
        dos(:class:`np.ndarray): estimate of density of states (DOS) evaluated
          at sampled energies
        energies(:class:`np.ndarray): sampled energies
        beta1(float): first inverse temperature
        beta2(float): second inverse temperature
    """
    energies = energies.ravel()
    log_Z1 = log_partition_function(dos, energies, beta1)
    log_Z2 = log_partition_function(dos, energies, beta2)
    g = np.add.outer(-energies * beta1, -energies * beta2)
    mins = np.min(np.dstack((g, g.T)), axis=2)
    integrand = mins + np.add.outer(dos, dos)

    return np.exp(log_sum_exp(integrand.ravel()) - log_Z1 - log_Z2)


def get_quantity_function(opt_quantity: OptimizationQuantity) -> Callable:
    """
    Looks up the optimization quantity function for a corresponding OptimizationQuantity
    enum.

    Args:
      opt_quantity: The optimization quantity type

    Raises:
      ValueError: If no matches were found for the specified `opt_quantity`.
    """
    if opt_quantity == OptimizationQuantity.ACCEPTANCE_RATE:
        return acceptance_rate
    else:
        raise ValueError(f"Unknown optimization quantity type: {opt_quantity}")
