"""
Classes for calculating a schedule given the density of states (DOS)
"""
from abc import abstractmethod, ABC

import numpy as np


class AbstractScheduleOptimizer(ABC):
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
        self._dos = dos
        self._energies = energies

    @abstractmethod
    def optimize(self):
        '''
        Estimates an optimized schedule.
        '''
        pass


class AbstractSingleParameterScheduleOptimizer(AbstractScheduleOptimizer):
    '''
    Interface for classes which estimate Replica Exchange schedules based on
    a single parameter.

    This works by trying to keep a certain quantity, which somehow describes an
    inverse "distance" between the distributions of neighboring replicas,
    constant between adjacent parameter values. Examples for this distance measure
    are the acceptance rate, the Kullback-Leibler divergence, the Hellinger
    distance, ...
    '''
    def __init__(self, dos, energies, optimization_quantity):
        '''
        Initializes a schedule optimizer.

        Args:
            dos(:class:`np.ndarray`): estimate of the DOS evaluated at energy
              samples
            energies(:class:`np.ndarray`): sampled energies from which the DOS
              estimate was calculated
            optimization_quantity(callable): calculates an optimization quantity
              such as the acceptance rate for two replicas at two different schedule
              parameter values given a DOS estimate and the corresponding
              sampled energies. Takes arguments ``(dos, energies, param1, param2)``.
        '''
        super().__init__(dos, energies)
        self._optimization_quantity = optimization_quantity

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
        delta = decrement
        while params[-1] >= min_param:
            est_q = self._optimization_quantity(self._dos, self._energies,
                                                params[-1], params[-1] - delta)
            if est_q <= target_value:
                params.append(params[-1] - delta)
                delta = decrement
            else:
                delta += decrement

        return {self._param_name: np.array(params)}


class BoltzmannOptimizer(
        AbstractSingleParameterScheduleOptimizer):
    _param_name = 'beta'
