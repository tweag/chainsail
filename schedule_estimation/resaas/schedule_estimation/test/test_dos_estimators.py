import unittest
import numpy as np
np.random.seed(42)

from resaas.schedule_estimation.dos_estimators import DefaultWHAM
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


class testDefaultWHAM(unittest.TestCase):
    def setUp(self):
        self.wham = DefaultWHAM(energies, lambda E, beta: -beta * E, schedule)

    def testRun(self):
        # TODO: replace this test (of the derived normalization constants) with a test
        # of the actual DOS estimate
        # TODO: maybe write unit test for WHAM, although it's probably rather difficult
        est_log_dos = self.wham.run()
        beta1 = schedule['beta'][0]
        beta2 = schedule['beta'][3]
        Z1 = np.sqrt(2 * np.pi / beta1)
        Z2 = np.sqrt(2 * np.pi / beta2)
        Z1_est = np.exp(log_sum_exp(-energies.ravel() * beta1 + est_log_dos))
        Z2_est = np.exp(log_sum_exp(-energies.ravel() * beta2 + est_log_dos))

        self.assertTrue(np.fabs(Z1 / Z2 - Z1_est / Z2_est) < 1e-2)
