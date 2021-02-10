import os

import numpy as np


def line(a, b, x): return a * x + b


def rn_average(r, n, axis):
    return np.sum(np.array(r) ** (-n), axis=axis) ** (-1/n)


class Posterior:
    def __init__(self, sigma_l, sigma_p, n, data_x, data_y):
        self.sigma_l = sigma_l
        self.sigma_p = sigma_p
        self.n = n
        self.data_x = data_x
        self.data_y = data_y

    def log_prior(self, x):
        inv_cov = np.eye(len(x)) / self.sigma_p / self.sigma_p
        return (-0.5 * x.T @ inv_cov @ x).sum()

    def log_likelihood(self, x):
        mock_y = line(x[0], x[1], self.data_x)
        return -0.5 * np.sum(rn_average(np.fabs(self.data_y - mock_y[:, None]), 6, axis=1) ** 2) \
          / self.sigma_l / self.sigma_l

    def log_prob(self, x):
        return self.log_likelihood(x) + self.log_prior(x)


path = os.path.dirname(__file__)
data = np.loadtxt(os.path.join(path, 'data.txt'))
pdf = Posterior(1, 5, 6, data[:,0], data[:,1:])
initial_state = np.random.uniform(-5, 5, size=2).ravel()
