'''
Classes which estimate the density of states (DOS) from MCMC samples from a
distribution at different "temperatures".
'''
import numpy as np
from abc import abstractmethod, ABCMeta


def log(text):
    '''
    Write a log entry.

    TODO: we might log to some database or a file instead of stdout
    '''
    print(text)


def log_sum_exp(x, axis=0):
    '''
    Calculate the log of a sum of exponentials in a numerically
    stable way
    '''
    xmax = x.max(axis)
    return np.log(np.exp(x - xmax).sum(axis)) + xmax


class AbstractWHAM(metaclass=ABCMeta):
    def __init__(self, energies, log_ensemble, parameters):
        '''
        Interface for classes implementing WHAM (TODO: link)

        :param energies: negative log-probabilities ('energies') from
                         from different ensembles
        :type energies: :class:`numpy.ndarray` of shape 
                        (# ensembles, # samples per ensemble)
        :param log_ensemble: logarithm of the probability density defining the
                             ensemble 
        :type log_ensemble: callable taking a single sample and a dictionary of
                            of parameters
        :param parameters: parameter values defining the ensemble at different
                           "temperatures"
        :type parameters: dict of parameter values. The keys are the parameter
                          names and the values :class:`numpy.ndarray`s with the
                          parameter values corresponding to the first dimension
                          of the `energies` argument
        '''
        self.energies = energies
        self.log_ensemble = log_ensemble
        self.parameters = parameters
        self.n_ensembles = energies.shape[0]

    def validate_shapes(self, energies, parameters):
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
        pass


class DefaultWHAM(AbstractWHAM):
    def calculate_log_qs(self):
        param_dicts = [{param: self.parameters[param][i] for param in
                        self.parameters} for i in range(self.n_ensembles)]
        log_qs = np.array([self.log_ensemble(self.energies.ravel(), **params)
                           for params in param_dicts])

        return log_qs

    def stopping_criterion(self, log_L, previous_log_L, termination_threshold):
        return abs(log_L - previous_log_L) / log_L < termination_threshold

    def calc_log_L(self, f, log_g):
        return -f.sum() + log_g.sum()
    
    def run(self, max_iterations=5000, threshold=1e-6):
        '''
        Do multiple histogram reweighting with infinitely fine binning as
        outlined in the paper "Evaluation of marginal likelihoods via the
        density of states" (Habeck, AISTATS 2012)

        :param n_iterations: how many WHAM iterations to perform
        :type n_iterations: int
        '''
        
        f = np.zeros(self.n_ensembles)
        log_qs = self.calculate_loq_qs()

        old_log_L = 1e300
        for i in range(max_iterations):
            log_gs = -log_sum_exp(log_qs + f[:, None], axis=0)
            log_gs -= log_sum_exp(log_gs)
            f = -log_sum_exp((log_qs + log_gs).T, axis=0)

            log_L = self.calc_log_L(f, log_gs)
            if i % 100 == 0:
                log('Likelihood: {}'.format(L))
            if self.stopping_criterion(log_L, old_log_L, threshold):
                break
            old_log_L = log_L
                
        if i > 0.8 * max_iterations:
            log(('More than 80% of max WHAM iterations were required. '
                 'Histogram reweighting might not have converged.'))

        return log_gs


class AbstractDOSCalculator(metaclass=ABCMeta):
    def __init__(self, wham_class=DefaultWHAM,
                 max_wham_iterations=5000, wham_threshold=1e-6):
        '''
        Defines the interface for classes which estimate the density
        of states (DOS) for different families of tempered distributions
        ("ensembles").
        '''
        self.wham_class = wham_class
        self.max_wham_iterations = max_wham_iterations
        self.wham_threshold = wham_threshold

    @abstractmethod
    def log_ensemble(self, energy):
        pass

    def calculate_dos(self, sampling_result, schedule, log_prob):
        energies = sampling_result['energies']
        wham = self.wham_class(energies, self.log_ensemble, schedule)
        log_dos = wham.run(self.max_wham_iterations, self.wham_threshold)

        return log_dos


class BoltzmannDOSCalculator(AbstractDOSCalculator):

    def make_log_ensemble(self, energy):
        return lambda energy, beta: -energy * beta
