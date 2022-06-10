import unittest
import numpy as np

np.random.seed(52)

from chainsail.schedule_estimation.dos_estimators import WHAM
from chainsail.common.tempering.ensembles import BoltzmannEnsemble
from chainsail.common.util import log_sum_exp

# draw samples from a bunch of normal distributions with standard deviations
# 1, 2, ...
sigmas = np.arange(1, 5, 0.1)
samples = np.array([np.random.normal(0, s, size=500) for s in sigmas])
# calculate the "energies"
energies = 0.5 * samples ** 2
# morph normal distributions into samples of harmonic oscillator at different
# inverse temperatures beta = 1 / sigma ** 2
schedule = {"beta": 1.0 / sigmas ** 2}


class testWHAM(unittest.TestCase):
    def setUp(self):
        self.wham = WHAM(BoltzmannEnsemble)

    def testDos(self):
        est_log_dos = self.wham.estimate_dos(energies, schedule, max_iterations=100)
        rebinned_dos, bins = np.histogram(
            energies.flatten(), weights=np.exp(est_log_dos), bins=100
        )
        mean_binned_energy = (bins[:-1] + bins[1:]) / 2

        # Normalize re-binned  DOS
        rebinned_dos[rebinned_dos == 0] = 1e-20
        rebinned_log_dos = np.log(rebinned_dos)
        rebinned_log_dos -= log_sum_exp(rebinned_log_dos)
        # Calculate expected log DOS
        expected_log_dos = np.log(2 / np.sqrt(2 * mean_binned_energy))
        # And normalize
        expected_log_dos -= log_sum_exp(expected_log_dos)
        # Only compare lower energies since higher energies are not adequately sampled
        cutoff = 20
        assert np.allclose(expected_log_dos[:cutoff], rebinned_log_dos[:cutoff], atol=0.5)
