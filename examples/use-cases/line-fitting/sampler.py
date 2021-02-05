import numpy as np


class RWMCSampler:

    def __init__(self, pdf, state, stepsize, timestep_adaption_limit=0,
                 adaption_uprate=1.05, adaption_downrate=0.95):

        self.pdf = pdf
        self.state = state
        self.stepsize = stepsize
        self.timestep_adaption_limit = timestep_adaption_limit
        self.adaption_uprate = adaption_uprate
        self.adaption_downrate = adaption_downrate
        self._last_move_accepted = False
        self._n_moves = 0

    def _adapt_stepsize(self):
        if self._last_move_accepted:
            self.stepsize *= self.adaption_uprate
        else:
            self.stepsize *= self.adaption_downrate

    def sample(self):

        E_old = -self.pdf.log_prob(self.state)
        proposal = self.state + np.random.uniform(low=-self.stepsize, high=self.stepsize)
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
