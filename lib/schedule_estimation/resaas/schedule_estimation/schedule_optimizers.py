"""
Classes for calculating a schedule given the density of states (DOS)
"""
from abc import abstractmethod, ABC

import numpy as np


def log(msg):
    print(msg)


class AbstractScheduleOptimizer(ABC):
    """
    Interface for classes which estimate Replica Exchange schedules based on
    a density of states (DOS) estimate.
    """

    def __init__(self, max_replicas):
        """
        Initializes a schedule optimizer.

        Args:
            max_replicas(int): maximum length of new schedule
        """
        self._max_replicas = max_replicas

    @abstractmethod
    def optimize(self, dos, energies):
        """
        Estimates an optimized schedule.
        Args:
            dos(:class:`np.ndarray`): estimate of the DOS evaluated at energy
              samples
            energies(:class:`np.ndarray`): sampled energies from which the DOS
              estimate was calculated
        """
        pass


class SingleParameterScheduleOptimizer(AbstractScheduleOptimizer):
    """
    Interface for classes which estimate Replica Exchange schedules based on
    a single parameter.

    This works by trying to keep a certain quantity, which somehow describes an
    inverse "distance" between the distributions of neighboring replicas,
    constant between adjacent parameter values. Examples for this distance measure
    are the acceptance rate, the Kullback-Leibler divergence, the Hellinger
    distance, ...
    """

    def __init__(
        self,
        target_value,
        max_param,
        min_param,
        decrement,
        optimization_quantity,
        param_name,
        max_replicas,
    ):
        """
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
            max_replicas(int): maximum length of new schedule
        """
        super().__init__(max_replicas)
        self._target_value = target_value
        self._max_param = max_param
        self._min_param = min_param
        self._decrement = decrement
        self._optimization_quantity = optimization_quantity
        self._param_name = param_name

    def _squeeze_parameters(self, parameters):
        """
        Linearly interpolates a too long parameter list to a length given by
        the maximum number of replicas.

        Args:
          parameters(np.array): list of ensemble parameters
        """
        n_params = len(parameters)
        max_replicas = self._max_replicas
        n_sampling_points = n_params * max_replicas * 100
        sampling_points = np.linspace(0, n_params, n_sampling_points)
        interpolated_params = np.interp(sampling_points, np.arange(len(parameters)), parameters)
        squeezed_params = interpolated_params[:: n_params * 100]
        return squeezed_params

    def optimize(self, dos, energies):
        """
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
        """
        params = [self._max_param]
        delta = self._decrement
        log("Optimizing schedule...")
        new_param_msg = (
            "Added new parameter to schedule. Value: " "{:.4f}, expected target value: {}"
        )

        def break_condition(old_param, delta):
            close = abs(old_param - delta - self._min_param) < 1e-8
            smaller = old_param - delta < self._min_param
            return close or smaller

        while not break_condition(params[-1], delta):
            new_param = params[-1] - delta
            est_q = self._optimization_quantity(dos, energies, params[-1], new_param)
            if est_q <= self._target_value:
                params.append(new_param)
                log(new_param_msg.format(new_param, est_q))
                delta = self._decrement
            else:
                delta += self._decrement
        else:
            params.append(self._min_param)
            est_q = self._optimization_quantity(dos, energies, params[-2], params[-1])
            log(new_param_msg.format(params[-1], est_q))

        if len(params) > self._max_replicas:
            params = self._squeeze_parameters(params)
            log(
                (
                    "Optimized schedule longer than allowed maximum number "
                    "of replicas. Schedule has been squeezed. Expect lower "
                    "acceptance rates."
                )
            )
        log(("Schedule optimization completed. Length of new schedule: " f"{len(params)}"))

        return {self._param_name: np.array(params)}
