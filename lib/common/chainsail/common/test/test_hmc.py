import unittest

import numpy as np

from chainsail.common.pdfs import AbstractPDF
from chainsail.common.samplers.hmc import _leapfrog, BasicHMCSampler
from chainsail.common.samplers.rwmc import RWMCSampler


class Normal(AbstractPDF):
    def log_prob(self, x):
        return -0.5 * np.sum(x**2)

    def log_prob_gradient(self, x):
        return -x


def test_leapfrog():
    """
    Tests leapfrog integration by integrating the equations of
    motion of a harmonic oscillator, for which the analytical solution
    is easy to calculate.
    """
    q0 = np.array([1.0])
    p0 = np.array([-1.0])

    def gradient(x):
        return x

    stepsize = 0.01
    num_steps = 1000

    result_q, result_p = _leapfrog(q0.copy(), p0.copy(), gradient, stepsize, num_steps)
    t_final = stepsize * num_steps

    expected_q = p0 * np.sin(t_final) + q0 * np.cos(t_final)
    assert np.isclose(result_q[0], expected_q[0], atol=1e-4)
    expected_p = p0 * np.cos(t_final) - q0 * np.sin(t_final)
    assert np.isclose(result_p[0], expected_p[0], atol=1e-4)


class TestSamplers(unittest.TestCase):
    """
    Functional test: sample from normal distribution
    """

    def setUp(self):
        self._pdf = Normal()
        self._initial_state = np.array([1.0])

    def _test_sampling(self, sampler, num_samples, test_adaption):
        stats = []
        samples = []
        for _ in range(num_samples):
            samples.append(sampler.sample())
            stats.append(sampler.last_draw_stats)
        samples = samples[sampler._num_adaption_samples :]
        self.assertTrue(-0.2 < np.mean(samples) < 0.2)
        self.assertTrue(0.8 < np.std(samples) < 1.2)

        if test_adaption:
            burnin = sampler._num_adaption_samples
            num_accepted = np.sum([x["x"].accepted for x in stats[burnin:]])
            stats_acceptance_rate = num_accepted / (num_samples - burnin)
            self.assertTrue(0.4 < stats_acceptance_rate < 0.6)

    def test_hmc_sampler(self):
        hmc = BasicHMCSampler(self._pdf, self._initial_state.copy(), 0.8, 10, 0)
        # due to the symmetries of the normal distribution, HMC can run into
        # issues: the stability limit is quite sharp, shortly before, the
        # the acceptance rate is essentially 1.0, sfortly after, it's
        # practically zero, so stepsize adaption is not useful here.
        self._test_sampling(hmc, num_samples=10000, test_adaption=False)

    def test_rwmc_sampler(self):
        rwmc = RWMCSampler(self._pdf, self._initial_state.copy(), 2.0, 15000, 1.02, 0.98)
        self._test_sampling(rwmc, num_samples=50000, test_adaption=True)
