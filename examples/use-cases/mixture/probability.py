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
        return logsumexp(np.log(self.weights) + log_gaussian(x, self.means, self.sigmas))

    def log_prob_gradient(self, x):
        outer = softmax(np.log(self.weights) + log_gaussian(x, self.means, self.sigmas))
        inner = log_gaussian_gradient(x, self.means, self.sigmas)
        return np.sum(outer[..., None] * inner, 0)


n_components = 4
# means = np.random.uniform(-3, 3, size=(n_components, 2))
means = np.array([[-1.0, -2.0], [1.0, 1.0], [3.0, 2.0], [2.0, -2.0]])
sigmas = np.ones(n_components) / 3
# weights = np.random.uniform(size=n_components)
weights = np.ones(n_components) / n_components
weights /= weights.sum()

pdf = GaussianMixture(means, sigmas, weights)
initial_states = np.array([-1.0, 0.5])
