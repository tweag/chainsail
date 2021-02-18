import os

import numpy as np


def line(a, b, x):
    return a * x + b


def line_gradient(a, b, x): return np.array((x, np.ones(len(x))))


def rn_average(r, n, axis):
    return np.sum(np.array(r) ** (-n), axis=axis) ** (-1 / n)


def rn_average_grad(r, n, axis):
    a = np.sum(np.array(r) ** (-n), axis=axis) ** (-1 / n - 1)
    return a[:, None] * np.array(r) ** (-n - 1)


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

    def log_prior_gradient(self, x):
        inv_cov = np.eye(len(x)) / self.sigma_p / self.sigma_p
        return -inv_cov @ x

    def log_likelihood(self, x):
        mock_y = line(x[0], x[1], self.data_x)
        return (
            -0.5
            * np.sum(rn_average(np.fabs(self.data_y - mock_y[:, None]), 6, axis=1) ** 2)
            / self.sigma_l
            / self.sigma_l
        )

    def log_likelihood_gradient(self, x):
        mock_y = line(x[0], x[1], self.data_x)
        r = self.data_y - mock_y[:, None]
        line_grad = line_gradient(x[0], x[1], self.data_x)
        num_ys = self.data_y.shape[1]
        abs_grad = (-r / np.fabs(r))[..., None] * np.tile(
            line_grad.T, num_ys).reshape(-1, num_ys, 2)
        outermost = -rn_average(np.fabs(r), self.n, axis=1)
        avg_grad = rn_average_grad(np.fabs(r), self.n, axis=1)
        inner = np.sum(avg_grad[..., None] * abs_grad, 1)
        return np.sum(outermost[:, None] * inner, 0)

    def log_prob(self, x):
        x = np.array(x)
        return self.log_likelihood(x) + self.log_prior(x)

    def log_prob_gradient(self, x):
        x = np.array(x)
        return (self.log_likelihood_gradient(x) + self.log_prior_gradient(x)).ravel()


path = os.path.dirname(__file__)
data = np.loadtxt(os.path.join(path, "data.txt"))
pdf = Posterior(1, 5, 6, data[:, 0], data[:, 1:])
initial_states = np.random.uniform(-5, 5, size=2).ravel()
