import numpy as np

from scipy.special import logsumexp


def log_gaussian(x, mu, sigma):
    return - 0.5 * np.sum((x - mu) ** 2, -1) / sigma ** 2 \
           - np.log(np.sqrt(2 * np.pi * sigma ** 2))


class GaussianMixture(object):
    def __init__(self, means, sigmas, weights):
        self.means = means
        self.sigmas = sigmas
        self.weights = weights

    def log_prob(self, x):
        return logsumexp(np.log(self.weights)
                         + log_gaussian(x, self.means, self.sigmas))


n_components = 4
means = np.random.uniform(-3, 3, size=(n_components, 2))
means = np.array([[-1.0, -2.0],
                  [1.0, 1.0],
                  [3.0, 2.0],
                  [2.0, -2.0]])
sigmas = np.ones(n_components) / 3
weights = np.random.uniform(size=n_components)
weights /= weights.sum()
weights = np.ones(n_components) / n_components
pdf = GaussianMixture(means, sigmas, weights)


# import matplotlib.pyplot as plt

# sl = 100
# grid = np.zeros((sl, sl))
# minn = -4
# maxx = 4
# for i, x in enumerate(np.linspace(minn, maxx, sl)):
#     for j, y in enumerate(np.linspace(minn, maxx, sl)):
#         grid[i, j] = np.exp(pdf.log_prob(np.array([x, y])))

# fig, ax = plt.subplots()
# ax.matshow(grid)
# plt.show()

initial_state = np.array([-1.0, 0.5])

# pdf = GaussianMixture(-1., 2, 0.5, 0.2, 0.3, 0.7)
# initial_state = np.array([-1.0])


from collections import namedtuple

RWMCSampleStats = namedtuple('RWMCSampleStats', 'accepted total stepsize')


class RWMCSampler:

    def __init__(self, pdf, state, stepsize, timestep_adaption_limit=0,
                 adaption_uprate=1.05, adaption_downrate=0.95,
                 variable_name='x'):

        self.pdf = pdf
        self._state = state
        self.variable_name = variable_name

        self.stepsize = stepsize
        self.timestep_adaption_limit = timestep_adaption_limit
        self.adaption_uprate = adaption_uprate
        self.adaption_downrate = adaption_downrate
        self._last_move_accepted = False
        self._n_moves = 0

    @property
    def last_draw_stats(self):

        return {self.variable_name: RWMCSampleStats(self._last_move_accepted, 
                                                    self._n_moves, self.stepsize)}

    @property
    def state(self):
        return self._state
    @state.setter
    def state(self, value):
        self._state = value

    def _adapt_stepsize(self):
        if self._last_move_accepted:
            self.stepsize *= self.adaption_uprate
        else:
            self.stepsize *= self.adaption_downrate

    def sample(self):
        E_old = -self.pdf.log_prob(self.state)
        proposal = self.state + np.random.uniform(
            low=-self.stepsize, high=self.stepsize, size=len(self.state))
        E_new = -self.pdf.log_prob(proposal)

        accepted = np.log(np.random.random()) < -(E_new - E_old)

        if accepted:
            self.state = proposal
            self._last_move_accepted = True
        else:
            self._last_move_accepted = False

        if self._n_moves < self.timestep_adaption_limit:
            self._adapt_stepsize()

        self._n_moves += 1

        return self.state
