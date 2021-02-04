import unittest

import numpy as np

from resaas.schedule_estimation.dos_estimators import WHAM, BoltzmannEnsemble
<<<<<<< HEAD
from resaas.re_job_controller.initial_setup import (draw_initial_states,
                                                    interpolate_timesteps)
=======
from resaas.re_job_controller.initial_setup import draw_initial_states
>>>>>>> 829c754... Forgot to git add the test


class MockStorage:
    def __init__(self, energies, states):
        self._energies = energies
        self._states = states

    def load_all_energies(self):
        return self._energies

    def load_all_samples(self):
        return self._states


class TestDrawInitialTimesteps(unittest.TestCase):
    def setUp(self):
        pass

    def test_draw_initial_timesteps(self):
        """
        Uses the physicist's best friend, the harmonic oscillator, a.k.a. the
        normal distribution, to test drawing reweighted samples.

        This currently draws samples, calculates the DOS using WHAM and feeds
        the result into draw_initial_timesteps.
        TODO: use analytical DOS and circumvent need for WHAM here.
        """
        n_samples = 2000
        betas = np.arange(1.0, 0.1, -0.1)
        # Assuming a Boltzmann ensemble, a harmonic oscillator (HO) at inverse
        # temperature beta corresponds to a normal distribution with standard
        # deviation sigma = 1 / np.sqrt(beta). We can thus draw samples from the
        # normal distribution instead and avoid actual simulation of the HO.
        samples = np.array(
            [np.random.normal(scale=1 / np.sqrt(beta), size=n_samples)
             for beta in betas])
        # potential energy of a harmonic oscillator with force constant 1 and
        # equilibrium position 0
        energies = 0.5 * samples ** 2

        # estimate microcanonical density of states (DOS) from energies
        wham = WHAM(BoltzmannEnsemble)
        dos = wham.estimate_dos(energies, {'beta': betas}, 500)

        # new inverse temperatures for which we want to draw states by
        # reweighting the previous ones. We could also draw samples from
        # outside the previous range, say, at beta=0.05, at the risk of worse
        # statistics
        new_betas = np.arange(1.0, 0.1, -0.2)
        storage = MockStorage(energies, samples)
        # we can draw more reweighted samples than we had original samples
        n_reweighted_samples = 2 * n_samples
        # each call of draw_initial_states produces one sample for each inverse
        # temperature beta. So we run this many times.
        dos_reweighted_samples = np.array(
            [draw_initial_states({'beta': new_betas}, storage, dos)
             for _ in range(n_reweighted_samples)])

        expected_means = np.zeros(len(new_betas))
        reweighted_means = dos_reweighted_samples.mean(0)
        self.assertTrue(np.allclose(
            expected_means, reweighted_means, atol=0.1))

        reweighted_stds = dos_reweighted_samples.std(0)
        # transform from standard deviations back to inverse temperatures
        reweighted_betas = 1 / reweighted_stds ** 2
        self.assertTrue(np.allclose(reweighted_betas, new_betas, atol=0.05))


class TestTimestepInterpolation(unittest.TestCase):
    def setUp(self):
        pass

    def test_interpolate_timesteps(self):
        old_schedule = {'beta': [1.0, 0.8, 0.6, 0.4, 0.2]}
        old_timesteps = [2, 4, 6, 8, 10]
        new_schedule = {'beta': [1.0, 0.7, 0.3]}

        new_timesteps = interpolate_timesteps(
            new_schedule, old_schedule, old_timesteps)
        expected = [2, 5, 9]
        self.assertTrue(np.allclose(new_timesteps, expected))

        bad_old_schedule = {'beta': [1.0, 3.0, 0.6, 0.4, 0.2]}
        old_timesteps = [2, 4, 6, 8, 10]
        new_schedule = {'beta': [1.0, 0.7, 0.3]}

        # non-monotonously decreasing parameter
        with self.assertRaises(ValueError):
            interpolate_timesteps(new_schedule, bad_old_schedule,
                                  old_timesteps)
        bad_new_schedule = {'beta': [1.0, 1.0, 0.3]}
        with self.assertRaises(ValueError):
            interpolate_timesteps(bad_new_schedule, old_schedule,
                                  old_timesteps)
        # non-equal number of parameters and time steps
        bad_timesteps = [0.9, 3]
        with self.assertRaises(ValueError):
            interpolate_timesteps(new_schedule, old_schedule,
                                  bad_timesteps)
