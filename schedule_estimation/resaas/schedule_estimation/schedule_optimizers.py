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


class SingleParameterScheduleOptimizer(AbstractScheduleOptimizer):
    '''
    Interface for classes which estimate Replica Exchange schedules based on
    a single parameter.

    This works by trying to keep a certain quantity, which somehow describes an
    inverse "distance" between the distributions of neighboring replicas,
    constant between adjacent parameter values. Examples for this distance measure
    are the acceptance rate, the Kullback-Leibler divergence, the Hellinger
    distance, ...
    '''

    def __init__(self, target_value, max_param, min_param, decrement,
                 optimization_quantity, param_name):
        '''
        Initializes a schedule optimizer.

        Args:
            target_value(float): target value for the quantity
            max_param(float): maximum parameter value to start iteration at
            min_param(float): minimum parameter value determining when
              iteration terminates
            decremet(float): parameter value decrement
            optimization_quantity(callable): calculates an optimization
              quantity such as the acceptance rate for two replicas at two
              different schedule parameter values given a DOS estimate and the
              corresponding sampled energies. Takes arguments
              ``(dos, energies, param1, param2)``.
            param_name(str): name of the
              schedule parameter to be optimized
        '''
        self._target_value = target_value
        self._max_param = max_param
        self._min_param = min_param
        self._decrement = decrement
        self._optimization_quantity = optimization_quantity
        self._param_name = param_name

    def optimize(self, dos, energies):
        '''
        Optimizes a Replica Exchange schedule based on some quantity such as an
        acceptance rate or a cross-entropy.

        Starting at ``self._max_param``, the parameter value is increasingly
        lowered and the quantity is calculated for each parameter value. If the
        quantity, as a function of the previously stored parameter value
        and the current value is below ``self._target_value``, the current
        value is stored and another iteration begins. That way, a parameter
        schedule is obtained, for which the target quantity between neighboring
        parameter values is approximately given by ``self._target_value``.

        Args:
            dos(:class:`np.ndarray`): estimate of the DOS evaluated at energy
              samples
            energies(:class:`np.ndarray`): sampled energies from which the DOS
              estimate was calculated
        '''
        params = [self._max_param]
        delta = self._decrement
        while params[-1] >= self._min_param:
            est_q = self._optimization_quantity(dos, energies,
                                                params[-1], params[-1] - delta)
            if est_q <= self._target_value:
                params.append(params[-1] - delta)
                delta = self._decrement
            else:
                delta += self._decrement

        return {self._param_name: np.array(params)}
