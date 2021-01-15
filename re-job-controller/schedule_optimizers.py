'''
Classes for calculating a schedule given the density of states
'''
import numpy as np
from abc import abstractmethod, ABCMeta

from util import log_sum_exp

class AbstractScheduleOptimizer(metaclass=ABCMeta):
    def __init__(self, dos, energies):
        self.dos = dos - log_sum_exp(dos)
        self.energies = energies

    @abstractmethod
    def optimize(self):
        pass


class SingleParameterScheduleOptimizer(AbstractScheduleOptimizer):
    @abstractmethod
    def estimate_target_quantity(self, last_param, test_param):
        pass

    def optimize(self, decrement, target_value, max_param, min_param):
        params = [max_param]
        previous_test_param = params[-1]

        while previous_test_param > min_param:
            current_test_param = previous_test_param - decrement
            estimated_quantity = self.estimate_target_quantity(
                params[-1], current_test_param)
            print(estimated_quantity)
            if estimated_quantity < target_value:
                params.append(previous_test_param)
            previous_test_param = current_test_param

        return {self._param_name: params}

class BoltzmannAcceptanceRateOptimizer(SingleParameterScheduleOptimizer):
    _param_name = 'beta'

    def log_Z(self, beta):
        return log_sum_exp(
            (-self.energies.ravel() * beta + self.dos).T, axis=0)
        
    
    def estimate_target_quantity(self, last_beta, test_beta):
        energies = self.energies.ravel()
        log_Z1 = self.log_Z(last_beta)
        log_Z2 = self.log_Z(test_beta)
        
        # g1 = np.array([[-E2 * last_beta - E1 * test_beta for E1 in energies]
        #                for E2 in energies])
        # g2 = np.array([[-E1 * last_beta - E2 * test_beta for E1 in energies]
        #                for E2 in energies])
        # mins = np.min(np.dstack((g1, g2)), axis=2)
        # integrand = mins + np.add.outer(self.dos, self.dos)
        integrand = np.array(
            [[min(-E1 * last_beta - E2 * test_beta,
                  -E2 * last_beta - E1 * test_beta)
              - l1 - l2 for (E1, l1) in zip(energies, self.dos)]
             for (E2, l2) in zip(energies, self.dos)])
        return np.exp(log_sum_exp(integrand.ravel()) - log_Z1 - log_Z2)
