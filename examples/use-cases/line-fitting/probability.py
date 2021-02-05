import numpy as np


def line(a, b, x): return a * x + b


def rn_average(r, n):
    r = r.T
    return np.sum(np.array(r) ** (-n), axis=-1) ** (-1/n)


def log_likelihood(params, sigma, x, y, n=6):
    mock_y = line(params[:, 0][:, None], params[:, 1][:, None], x)
    return -0.5 * np.sum(rn_average(np.fabs(y - mock_y), 6) ** 2) / sigma / sigma


def log_prior(params, sigma):
    inv_cov = np.eye(len(params)) / sigma / sigma
    return (-0.5 * params.T @ inv_cov @ params).sum()


def log_posterior(params, x, y, sigma_l, sigma_p, n):
    return log_likelihood(params, x, y, sigma_l, n) + log_prior(params, sigma_p)


class Posterior:
    def __init__(self, sigma_l, sigma_p, n, data_x, data_y):
        self.sigma_l = sigma_l
        self.sigma_p = sigma_p
        self.n = n
        self.data_x = data_x
        self.data_y = data_y

    def log_prob(self, x):
        log_l = log_likelihood(x, self.sigma_l, self.data_x, self.data_y, self.n)
        log_p = log_prior(x, self.sigma_p)
        return log_l + log_p


x_data, y_data = np.loadtxt('data.txt').T

pdf = Posterior(1, 5, 6, x_data, y_data)
