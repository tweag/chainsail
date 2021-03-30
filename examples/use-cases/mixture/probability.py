"""
Example probability density for consumption by RESAAS
"""

# you can use any pip-installable Python module you like,
# as long as it hasn't any system dependencies.
# Just make sure to add it to the list of dependencies
# in the job sumission form
import numpy as np
from scipy.special import logsumexp, softmax


def log_gaussian(x, mu, sigma):
    Z = np.log(np.sqrt(2 * np.pi * sigma ** 2))
    return -0.5 * np.sum((x - mu) ** 2, -1) / sigma ** 2 - Z


def log_gaussian_gradient(x, mu, sigma):
    return (x - mu) / sigma[:, None] ** 2


class GaussianMixture(object):
    def __init__(self, means, sigmas, weights):
        self.means = means
        self.sigmas = sigmas
        self.weights = weights

    def log_prob(self, x):
        # you _have_ to implement a log_prob method for your probability density.
        # It evaluates the log-probability of the distributionb you want to sample
        return logsumexp(np.log(self.weights) + log_gaussian(x, self.means, self.sigmas))

    def log_prob_gradient(self, x):
        # you _have_ to implement a log_prob_gradient method for your probability density.
        # It evaluates the gradient of the log-probability of the distributionb you want to sample.
        # This is required for Hamiltonian Monte Carlo (HMC) sampling.
        outer = softmax(np.log(self.weights) + log_gaussian(x, self.means, self.sigmas))
        inner = log_gaussian_gradient(x, self.means, self.sigmas)
        return np.sum(outer[..., None] * inner, 0)


means = np.array([[-1.0, -2.0], [1.0, 1.0], [3.0, 2.0], [2.0, -2.0]])
n_components = len(means)
sigmas = np.ones(n_components) / 3
weights = np.ones(n_components) / n_components
weights /= weights.sum()

# This is what you have to provide and what RESAAS will import:
# - an object `pdf` with methods `log_prob` and `log_prob_gradient`,
#   each taking a single, flat numpy array as its argument
# - a flat numpy array `intial_states` with an initial state for the
#   MCMC chains. Here we have two parameters, so the length of that
#   array is two
pdf = GaussianMixture(means, sigmas, weights)
initial_states = np.array([-1.0, 0.5])
