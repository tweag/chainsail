import unittest

import numpy as np

from chainsail.schedule_estimation.optimization_quantities import (
    acceptance_rate,
    log_partition_function,
)


class testOptimizationQuantities(unittest.TestCase):
    """
    Test acceptance rate and partition function by using the harmonic
    oscillator as a toy example. A harmonic oscillator with E = 0.5 * x ** 2
    corresponds, with the identification E = -log p(x), to a normal
    distribution.
    """

    def setUp(self):
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
        self._log_dos = np.log(2 / np.sqrt(2 * E_mean) * delta)
        self._energies = E_mean

    def testAcceptanceRate(self):
        beta1 = 1.0
        beta2 = 1.0 / 3.0 ** 2
        result = acceptance_rate(self._log_dos, self._energies, beta1, beta2)
        # obtained from numerical integration
        # TODO: figure out what the analytical expression (it's probably some
        # erfc stuff) is and generalize this test.
        expected = 0.4096

        self.assertAlmostEqual(result, expected, places=2)

    def testLogPartitionFunction(self):
        beta1 = 1.0
        beta2 = 1.0 / 3.0 ** 2
        est_Z1 = log_partition_function(self._log_dos, self._energies, beta1)
        est_Z2 = log_partition_function(self._log_dos, self._energies, beta2)
        true_Z1 = np.sqrt(2 * np.pi / beta1)
        true_Z2 = np.sqrt(2 * np.pi / beta2)

        self.assertAlmostEqual(est_Z1, np.log(true_Z1), places=2)
        self.assertAlmostEqual(est_Z2, np.log(true_Z2), places=2)
