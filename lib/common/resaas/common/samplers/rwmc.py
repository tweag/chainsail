"""
A Metropolis-Hastings sampler as an example for the sampler interface
"""
from collections import namedtuple

import numpy as np

from resaas.common.samplers import AbstractSampler


RWMCSampleStats = namedtuple("RWMCSampleStats", "accepted stepsize neg_log_prob")


class RWMCSampler(AbstractSampler):
    """
    A simple Metropolis sampler with a uniform proposal distribution.
    """

    def __init__(
        self,
        pdf,
        state,
        stepsize,
        num_adaption_samples=0,
        adaption_uprate=1.05,
        adaption_downrate=0.95,
    ):
        """Initialize a Metropolis sampler.

        Args:
          pdf(AbstractPDF): an object representting a PDF with the interface
              defined in ``rexfw.pdfs``
          state(np.ndarray): initial state
          stepsize(float): integration stepsize for the integrator
          num_steps(int): number of integration steps the integrator performs
          num_adaption_samples(int): number of samples which to stop
              automatically adapting the stepsize
          adaption_uprate(float): factor with which to multiply current step
              size in case of rejected move
          adaption_downrate: factor with which to multiply current stepsize in
              case of accepted move
        """
        super(RWMCSampler, self).__init__(pdf, state)

        self._stepsize = stepsize
        self._num_adaption_samples = num_adaption_samples
        self._adaption_uprate = adaption_uprate
        self._adaption_downrate = adaption_downrate
        self._last_move_accepted = False
        self._sample_counter = 0

    @property
    def last_draw_stats(self):

        return {
            self.VARIABLE_NAME: RWMCSampleStats(
                self._last_move_accepted, self._stepsize, -self.pdf.log_prob(self.state)
            )
        }

    def _adapt_stepsize(self):
        """
        Increases / decreasese the leap frog stepsize depending on
        whether the last move has been rejected / accepted.
        """
        if self._last_move_accepted:
            self._stepsize *= self._adaption_uprate
        else:
            self._stepsize *= self._adaption_downrate

    def sample(self):
        """Draws a single sample."""
        E_old = -self.pdf.log_prob(self.state)
        proposal = self.state + np.random.uniform(
            low=-self._stepsize, high=self._stepsize, size=len(self.state)
        )
        E_new = -self.pdf.log_prob(proposal)
        accepted = np.log(np.random.random()) < -(E_new - E_old)

        if accepted:
            self.state = proposal

        self._last_move_accepted = accepted
        if self._sample_counter < self._num_adaption_samples:
            self._adapt_stepsize()
        self._sample_counter += 1

        return self.state
