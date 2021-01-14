'''
Classes for calculating a schedule given the density of states
'''

from abc import abstractmethod, ABCMeta

class AbstractScheduleOptimizer(metaclass=ABCMeta):
    def __init__(self, dos, energies):
        self.dos = dos
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
            print(current_test_param)
            estimated_quantity = self.estimate_target_quantity(
                params[-1], current_test_param)
            if estimated_quantity < target_value:
                params.append(previous_test_param)
            previous_test_param = current_test_param

        return {self._param_name: params}

class BoltzmannAcceptanceRateOptimizer(SingleParameterScheduleOptimizer):
    _param_name = 'beta'

    def estimate_target_quantity(self, last_beta, test_beta):
        log_Z1 = -log_sum_exp(
            (-self.energies.ravel() * last_beta + self.dos).T, axis=0)
        log_Z2 = -log_sum_exp(
            (-self.energies.ravel() * test_beta + self.dos).T, axis=0)
        g1 = np.array([[-E1 * last_beta - E2 * test_beta for E1 in energies]
                       for E2 in energies])
        g2 = np.array([[-E2 * last_beta - E1 * test_beta for E1 in energies]
                       for E2 in energies])
        mins = np.min(np.dstack((g1, g2)))
        integrand = mins - np.subtract.outer(self.dos, self.dos)
        return np.exp(log_sum_exp(integrand) - log_Z1 - log_Z2)
                      
