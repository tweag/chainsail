"""
A naive implementation of Hamiltonian Monte Carlo.
"""
from collections import namedtuple

import numpy as np

from resaas.common.samplers import AbstractSampler


HMCSampleStats = namedtuple("HMCSampleStats", "accepted stepsize neg_log_prob")


def _leapfrog(q, p, gradient, stepsize, num_steps):
    """
    Performs leap frog integration of Hamiltonian dynamics guided
    by the gradient of a potential energy

    Args:
      q(np.ndarray): initial position
      p(np.ndarray): initial momentum

    Returns:
      np.ndarray: position at the end of the trajectory
      np.ndarray: momentum at the end of the trajectory
    """
    p -= 0.5 * stepsize * gradient(q)

    for i in range(num_steps - 1):
        q += p * stepsize
        p -= stepsize * gradient(q)

    q += p * stepsize
    p -= 0.5 * stepsize * gradient(q)

    return q, p


class BasicHMCSampler(AbstractSampler):
    """
    A naive HMC sampler with unit mass matrix and a simple stepsize
    adaption scheme.
    """

    def __init__(
        self,
        pdf,
        state,
        stepsize,
        num_steps,
        num_adaption_samples=0,
        adaption_uprate=1.05,
        adaption_downrate=0.95,
        integrator=_leapfrog,
    ):
        """
        Initialize a HMC sampler.

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
          integrator(callable): function which performs symplectic integration
        """
        super().__init__(pdf, state)
        self._stepsize = stepsize
        self._num_steps = num_steps
        self._num_adaption_samples = num_adaption_samples
        self._adaption_uprate = adaption_uprate
        self._adaption_downrate = adaption_downrate
        self._last_move_accepted = 0
        self._n_accepted = 0
        self._samples_counter = 0

    @property
    def last_move_accepted(self):
        """Returns whether the last move has been accepted or not."""
        return self._last_move_accepted

    def _integrate(self, q, p):
        """Performs symplectic integration.

        This private method allows to swap out the default leapfrog integrator
        for, e.g., a higher-order scheme.

        Args:
          q(np.ndarray): initial position
          p(np.ndarray): initial momentum

        Returns:
          np.ndarray: position at the end of the trajectory
          np.ndarray: momentum at the end of the trajectory
        """
        return _leapfrog(
            q, p, lambda x: -self.pdf.log_prob_gradient(x), self._stepsize, self._num_steps
        )

    def _total_energy(self, q, p):
        return -self._pdf.log_prob(q) + 0.5 * np.sum(p ** 2)

    def sample(self):
        """Draws a single sample."""
        q = self.state.copy()
        p = np.random.normal(size=q.shape)

        E_old = self._total_energy(q, p)
        q, p = self._integrate(q, p)
        E_new = self._total_energy(q, p)  #
        accepted = np.log(np.random.uniform()) < -(E_new - E_old)

        if accepted:
            self.state = q

        self._last_move_accepted = accepted
        if self._samples_counter < self._num_adaption_samples:
            self._adapt_stepsize()
        self._samples_counter += 1

        return self.state

    @property
    def last_draw_stats(self):
        """Returns information about the most recently performed move.

        This is used by rexfw to log sampling statistics and also useful
        when embedding this HMC sampler in a Gibbs sampling scheme.

        Returns:
          dict: a single key with the (constant) variable name and an
              HMCSampleStats instance as its value
        """
        return {
            self.VARIABLE_NAME: HMCSampleStats(
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


if __name__ == "__main__":

    class HO:
        def log_prob(self, x):
            return -0.5 * np.sum(x ** 2)

        def log_prob_gradient(self, x):
            return -x

    init_state = np.array([0.0, 1.0])
    s = BasicHMCSampler(HO(), init_state, 0.5, 10)
    samples = np.array([s.sample() for _ in range(10000)])

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    from scipy.stats import norm

    for i, x in enumerate(init_state):
        ax.hist(samples[:, i], bins=40, alpha=0.5, density=True)
    xspace = np.linspace(-3, 3, 100)
    ax.plot(xspace, norm.pdf(xspace))
    plt.show()
