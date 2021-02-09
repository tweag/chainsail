import os

import numpy as np
from scipy.special import logsumexp, softmax


path = os.path.abspath(__file__)
data = np.loadtxt(os.path.join(path, "data.txt")).T


class Pdf:
    def __init__(self, num_clusters, sigma_likelihood, sigma_prior, prior_mean,
                 n_dim, data):
        self.num_clusters = num_clusters
        self.sigma_likelihood = sigma_likelihood
        self.sigma_prior = sigma_prior
        self.prior_mean = prior_mean
        self.n_dim = n_dim
        self.data = data

    def log_prior(self, x):
        x = x.reshape(-1, self.n_dim)
        return -0.5 * np.sum((x - self.prior_mean) ** 2, 1).sum() \
          / self.sigma_prior ** 2

    def log_prior_gradient(self, x):
        x = x.reshape(-1, self.n_dim)
        bla = -(x - self.prior_mean[None, :]) / self.sigma_prior ** 2
        return bla.ravel()

    def log_likelihood(self, x):
        x = x.reshape(-1, self.n_dim)
        a = logsumexp(-0.5 * np.sum((x[:, None] - self.data) ** 2, 2) \
                      / (self.sigma_likelihood ** 2), 0)
        return a.sum()

    def log_likelihood_gradient(self, x):
        x = x.reshape(-1, self.n_dim)
        d_outer = softmax(
            -0.5 * np.sum((x[:, None] - self.data) ** 2, 2)
            / (self.sigma_likelihood ** 2), axis=0)
        im = -(x[:, None] - self.data) * d_outer[..., None]
        return im.sum(1).ravel()

    def log_prob(self, x):
        x = x.reshape(-1, self.n_dim)
        return self.log_likelihood(x) + self.log_prior(x)

    def log_prob_gradient(self, x):
        return self.log_prior_gradient(x) + self.log_likelihood_gradient(x)


pdf = Pdf(9, 0.75, 5, np.array([1, 1]), data.shape[1], data)
initial_state = np.random.uniform(0, 1, size=pdf.num_clusters * pdf.n_dim)
initial_state = np.array([[0.0, 0.0],
                          [3.0, 0.0],
                          [0.0, 3.0],
                          [3.0, 3.0]]).ravel()
