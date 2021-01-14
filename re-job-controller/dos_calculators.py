import numpy as np
from abc import abstractmethod, ABCMeta

def log(text):
    print(text)

def log_sum_exp(x, axis=0):
    """
    Calculate the log of a sum of exponentials in a numerically
    stable way
    """
    xmax = x.max(axis)
    return np.log(np.exp(x - xmax).sum(axis)) + xmax


def WHAM(samples, log_ensemble, parameters, n_iterations):
    """
    Do multiple histogram reweighting with infinitely fine binning as outlined
    in the paper "Evaluation of marginal likelihoods via the density of states"
    (Habeck, AISTATS 2012)

    Arguments:
    - samples: numpy array of shape (# ensembles, # samples per ensemble)
               containing samples from different ensembles
    - log_ensemble: a function taking a single sample and a dictionary of
                    of parameters defining the family of ensembles
    - parameters: dictionary of parameter values. The keys are the parameter
                  names and the values numpy arrays with the parameter values
                  corresponding to the first dimension of the "samples" argument
    - n_iterations: how many WHAM iterations to perform

    Returns:
    - log_g: normalized density of states evaluated at the samples
    - f: logarithm of the normalization constants of the ensembles
    """
    n_replicas = samples.shape[0]
    param_dicts = [{param: parameters[param][i] for param in parameters}
                   for i in range(n_replicas)]
    log_q = np.array([log_ensemble(samples.ravel(), **params)
                      for params in param_dicts])

    f = np.zeros(n_replicas)

    def calc_L(f, log_g):
        return -f.sum() + log_g.sum()

    for i in range(n_iterations):
        log_g = -log_sum_exp(log_q + f[:, None], axis=0)
        log_g -= log_sum_exp(log_g)
        f = -log_sum_exp((log_q + log_g).T, axis=0)

        L = calc_L(f, log_g)
        if i % 100 == 0:
            log('Likelihood: {}'.format(L))

    if i > 0.8 * n_iterations:
        log(('More than 80% of max WHAM iterations were required. '
             'Histogram reweighting might not have converged.'))
            
    return log_g


class DOSCalculator(metaclass=ABCMeta):
    n_iterations = 5000

    def __init__(self):
        pass

    def fetch_probability_definition(self, probability_definition):
        pass
    
    @abstractmethod
    def make_log_ensemble(self, probability_definition):
        pass
        
    def calculate_dos(self, sampling_result, schedule, probability_definition):
        samples = self.load_samples(sampling_result['samples'])
        log_ensemble = self.make_log_ensemble(probability_definition)
        log_dos = WHAM(samples, log_ensemble, schedule, self.n_iterations)
                       
        return log_dos


class BoltzmannDOSCalculator(DOSCalculator):
    
    def make_log_ensemble(self, probability_definition):
        path = self.fetch_probability_definition(probability_definition)
        sys.path.append(path)
        from pdf_definition import log_prob
        return lambda x, beta: log_prob(x) * beta
