import os

import numpy as np


def line(a, b, x): return a * x + b


def rn_average(r, n):
    r = r.T
    return np.sum(np.array(r) ** (-n), axis=-1) ** (-1/n)


class Posterior:
    def __init__(self, sigma_l, sigma_p, n, data_x, data_y):
        self.sigma_l = sigma_l
        self.sigma_p = sigma_p
        self.n = n
        self.data_x = data_x
        self.data_y = data_y

    def log_prior(self, x):
        x = x.reshape(-1, 2)
        inv_cov = np.eye(len(x)) / self.sigma_p / self.sigma_p
        return (-0.5 * x.T @ inv_cov @ x).sum()

    def log_likelihood(self, x):
        x = x.reshape(-1, 2)
        mock_y = line(x[:, 0][:, None], x[:, 1][:, None], self.data_x)
        return -0.5 * np.sum(rn_average(np.fabs(self.data_y - mock_y), 6) ** 2) \
          / self.sigma_l / self.sigma_l

    def log_prob(self, x):
        x = x.reshape(-1, 2)
        return self.log_likelihood(x) + self.log_prior(x)


path = os.path.dirname(__file__)
x_data, y_data = np.loadtxt(os.path.join(path, 'data.txt')).T
pdf = Posterior(1, 5, 6, x_data, y_data)
initial_state = np.random.uniform(-5, 5, (1, 2)).ravel()
