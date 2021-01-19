"""
Classes for calculating a schedule given the density of states (DOS)
"""
import numpy as np
from abc import abstractmethod, ABCMeta

from util import log_sum_exp


class AbstractScheduleOptimizer(metaclass=ABCMeta):
    '''
    Interface for classes which estimate Replica Exchange schedules based on
    a density of states (DOS) estimate.
    '''
    def __init__(self, dos, energies):
        '''
        Initializes a schedule optimizer.

        Args:
            dos(:class:`np.ndarray`): estimate of the DOS evaluated at energy
              samples
            energies(:class:`np.ndarray`): sampled energies from which the DOS
              estimate was calculated
        '''
        self.dos = dos
        self.energies = energies

    @abstractmethod
    def optimize(self):
        '''
        Estimates an optimized schedule.
        '''
        pass


class SingleParameterScheduleOptimizer(AbstractScheduleOptimizer):
    @abstractmethod
    def estimate_target_quantity(self, param1, param2):
        '''
        Estimates some target quantity (acceptance rate, cross entropy, ...)
        for two values of the replica parameter.
        '''
        pass

    def optimize(self, target_value, max_param, min_param, decrement):
        '''
        Optimizes a Replica Exchange schedule based on some quantity such as an
        acceptance rate or a cross-entropy.

        Starting at max_param, the parameter value is increasingly lowered and
        the quantity is calculated for each parameter value. If the
        quantity, as a function of the previously stored parameter value
        and the current value is below ``target_value``, the current value is
        stored and another iteration begins. That way, a parameter schedule is
        obtained, for which the target quantity between neighboring parameter
        values is approximately given by ``target_value``.

        Args:
            target_value(float): target value for the quantity
            max_param(float): maximum parameter value to start iteration at
            min_param(float): minimum parameter value determining when
              iteration terminates
            decremet(float): parameter value decrement
        '''
        params = [max_param]
        previous_test_param = params[-1]

        while previous_test_param > min_param:
            current_test_param = previous_test_param - decrement
            estimated_quantity = self.estimate_target_quantity(
                params[-1], current_test_param)
            if estimated_quantity < target_value:
                params.append(previous_test_param)
            previous_test_param = current_test_param

        return {self._param_name: params}


class BoltzmannAcceptanceRateOptimizer(SingleParameterScheduleOptimizer):
    _param_name = 'beta'

    def log_Z(self, beta):
        '''
        Calculates an estimate of the partition function.

        Uses the DOS estimate to calculate an estimate of the partition
        function Z(beta) at a given inverse temperature beta.

        Args:
            beta(float): inverse temperature
        '''
        return log_sum_exp(
            (-self.energies.ravel() * beta + self.dos).T, axis=0)

    def estimate_target_quantity(self, beta1, beta2):
        '''
        Estimates acceptance rate between two neighboring replicas.

        Uses the DOS estimate to calculate the expected acceptance rate
        between two replicas in a Boltzmann schedule with inverse temperatures
        ``beta1`` and ``beta2``.

        Args:
            beta1(float): first inverse temperature
            beta2(float): second inverse temperature
        '''
        energies = self.energies.ravel()
        log_Z1 = self.log_Z(beta1)
        log_Z2 = self.log_Z(beta2)
        g = np.add.outer(-energies * beta1, -energies * beta2)
        mins = np.min(np.dstack((g, g.T)), axis=2)
        integrand = mins + np.add.outer(self.dos, self.dos)

        return np.exp(log_sum_exp(integrand.ravel()) - log_Z1 - log_Z2)
