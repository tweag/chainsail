import unittest
from itertools import cycle

import numpy as np

from chainsail.controller.initial_setup import draw_initial_states, interpolate_stepsizes


class MockStorage:
    def __init__(self, energies, states):
        self._energies = energies
        self._states = states

    def load_all_energies(self, from_sample, step):
        return self._energies

    def load_all_samples(self, from_sample, step):
        return self._states


class TestDrawInitialStepsizes(unittest.TestCase):
    """
    Uses the physicist's best friend, the harmonic oscillator, a.k.a. the
    normal distribution, to test drawing reweighted samples.
    """

    def setUp(self):
        pass

    def test_draw_initial_stepsizes(self):
        # In the Boltzmann ensemble, energies are exponentially distributed.
        # If we use np.linspace, we get too few energies close to zero.
        # That's why we use np.logspace.
        E = np.logspace(np.log(0.0001), np.log(30), 5000, base=10)
        # But this also means that energies are not equidistant. So for the
        # numerical integrations performed in the acceptance rate and
        # partition function, we have to reweight the analytical density
        # of states of the harmonic oscillator, given by
        # g(E) = 2 / \sqrt(2 * E), with the difference between neighboring
        # energies.
        E_mean = 0.5 * (E[1:] + E[:-1])
        delta = E[1:] - E[:-1]
        dos = np.log(2 / np.sqrt(2 * E_mean) * delta)
        energies = E_mean

        # Here's the fun part: now that we have energies, we need to get
        # "samples". So because E = 0.5 * x ** 2, for each energy we have two
        # possible samples x = +/- \sqrt(2 * E). So we alternate between
        # generating "+" samples and "-" samples.
        c = cycle((-1, 1))
        samples = np.array([next(c) * np.sqrt(2 * e) for e in energies])
        # new inverse temperatures for which we want to draw states by
        # reweighting the previous ones. We could also draw samples from
        # outside the previous range, say, at beta=0.05, at the risk of worse
        # statistics
        new_betas = np.arange(1.0, 0.1, -0.2)
        storage = MockStorage(energies, samples)
        # we can draw more reweighted samples than we had original samples
        n_reweighted_samples = 3000
        # each call of draw_initial_states produces one sample for each inverse
        # temperature beta. So we run this many times.
        dos_reweighted_samples = np.array(
            [
                draw_initial_states({"beta": new_betas}, storage, dos, 0, 1)
                for _ in range(n_reweighted_samples)
            ]
        )

        expected_means = np.zeros(len(new_betas))
        reweighted_means = dos_reweighted_samples.mean(0)
        self.assertTrue(np.allclose(expected_means, reweighted_means, atol=0.1))

        reweighted_stds = dos_reweighted_samples.std(0)
        # transform from standard deviations back to inverse temperatures
        reweighted_betas = 1 / reweighted_stds**2
        self.assertTrue(np.allclose(reweighted_betas, new_betas, atol=0.1))


class TestStepsizeInterpolation(unittest.TestCase):
    def setUp(self):
        pass

    def test_interpolate_stepsizes(self):
        old_schedule = {"beta": [1.0, 0.8, 0.6, 0.4, 0.2]}
        old_stepsizes = [2, 4, 6, 8, 10]
        new_schedule = {"beta": [1.0, 0.7, 0.3]}

        new_stepsizes = interpolate_stepsizes(new_schedule, old_schedule, old_stepsizes)
        expected = [2, 5, 9]
        self.assertTrue(np.allclose(new_stepsizes, expected))

        bad_old_schedule = {"beta": [1.0, 3.0, 0.6, 0.4, 0.2]}
        old_stepsizes = [2, 4, 6, 8, 10]
        new_schedule = {"beta": [1.0, 0.7, 0.3]}

        # non-monotonously decreasing parameter
        with self.assertRaises(ValueError):
            interpolate_stepsizes(new_schedule, bad_old_schedule, old_stepsizes)
        bad_new_schedule = {"beta": [1.0, 1.0, 0.3]}
        with self.assertRaises(ValueError):
            interpolate_stepsizes(bad_new_schedule, old_schedule, old_stepsizes)
        # non-equal number of parameters and stepsizes
        bad_stepsizes = [0.9, 3]
        with self.assertRaises(ValueError):
            interpolate_stepsizes(new_schedule, old_schedule, bad_stepsizes)
