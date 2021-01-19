import unittest
import numpy as np

from resaas.schedule_estimation.dos_calculators import DefaultWHAM

# draw samples from a bunch of normal distributions with standard deviations
# 1, 2, ...
sigmas = np.arange(1, 5)
samples = np.array([np.random.normal(0, s, size=200) for s in sigmas])
# calculate the "energies"
energies = 0.5 * samples ** 2
# morph normal distributions into samples of harmonic oscillator at different
# inverse temperatures beta = 1 / sigma ** 2
schedule = {'beta': 1.0 / sigmas ** 2}


class testDefaultWHAM(unittest.testCase):
    def setUp(self):
        self.wham = DefaultWHAM(energies, lambda E, beta: -beta * E, schedule)

    def testRun(self):
        est_log_dos = self.wham.run()
        def real_dos(E): return np.log(2) - 0.5 * np.log(E)
        real_log_dos_at_energies = real_dos(energies.ravel())
        self.assertTrue(np.all(est_log_dos / real_log_dos_at_energies  < 1e-3))
