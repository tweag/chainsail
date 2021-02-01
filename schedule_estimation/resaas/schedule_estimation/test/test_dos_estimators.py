import unittest
import numpy as np
np.random.seed(42)

from resaas.schedule_estimation.dos_estimators import (WHAM,
                                                       BoltzmannEnsemble)
from resaas.common.util import log_sum_exp

# draw samples from a bunch of normal distributions with standard deviations
# 1, 2, ...
sigmas = np.arange(1, 5)
samples = np.array([np.random.normal(0, s, size=1000) for s in sigmas])
# calculate the "energies"
energies = 0.5 * samples ** 2
# morph normal distributions into samples of harmonic oscillator at different
# inverse temperatures beta = 1 / sigma ** 2
schedule = {'beta': 1.0 / sigmas ** 2}


class testWHAM(unittest.TestCase):
    def setUp(self):
        self.wham = WHAM(BoltzmannEnsemble)

    def testEstimateDos(self):
        # TODO: replace this test (of the derived normalization constants) with
        # a test of the actual DOS estimate
        # Also maybe write unit test for WHAM, although it's probably rather
        # difficult
        est_log_dos = self.wham.estimate_dos(energies, schedule)
        beta1 = schedule['beta'][0]
        beta2 = schedule['beta'][3]
        Z1 = np.sqrt(2 * np.pi / beta1)
        Z2 = np.sqrt(2 * np.pi / beta2)
        Z1_est = np.exp(log_sum_exp(-energies.ravel() * beta1 + est_log_dos))
        Z2_est = np.exp(log_sum_exp(-energies.ravel() * beta2 + est_log_dos))

        self.assertTrue(np.fabs(Z1 / Z2 - Z1_est / Z2_est) < 1e-2)

    def testDos(self): 
        est_log_dos = self.wham.estimate_dos(energies, schedule)
        rebinned_log_dos, bins = np.histogram(energies.flatten(), weights=np.exp(est_log_dos), bins=100)
        mean_binned_energy = (bins[:-1] + bins[1:]) / 2

        # Normalize re-binned log DOS
        rebinned_log_dos = rebinned_log_dos - log_sum_exp(rebinned_log_dos)
        
        # Calculate expected log DOS
        expected_log_dos = np.log(2 / np.sqrt(2 * mean_binned_energy)).flatten()
        # And normalize
        expected_log_dos = expected_log_dos - log_sum_exp(expected_log_dos)
        
        print(expected_log_dos[:20] - rebinned_log_dos[:20])
        # TODO: This difference is a bit high
         # Only compare lower energies since higher energies are not adequately sampled
        np.testing.assert_almost_equal(expected_log_dos, rebinned_log_dos, decimal=5)
