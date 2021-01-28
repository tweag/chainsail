import os
import sys
import unittest
from pickle import load

import numpy as np

from resaas.schedule_estimation.optimization_quantities import (
    acceptance_rate,
    log_partition_function)

# TODO: replace estimated DOS by analytical DOS once confusion about
# estimated DOS being wrong but giving correct results downstream is
# lifted
DATA_PATH = (os.path.dirname(sys.modules[__name__].__file__)
             + '/dos_energies.pickle')


class testOptimizationQuantities(unittest.TestCase):
    def setUp(self):
        with open(DATA_PATH, "rb") as ipf:
            self.energies, self.dos = load(ipf)

    def testAcceptanceRate(self):
        beta1 = 1.0
        beta2 = 1.0 / 3.0 ** 2
        result = acceptance_rate(self.dos, self.energies, beta1, beta2)
        # obtained from numerical integration
        # TODO: figure out what the analytical expression is and generalize
        # this test.
        expected = 0.4096

        self.assertAlmostEqual(result, expected, places=2)

    def testLogPartitionFunction(self):
        # partition functions (=normalization constants) can be estimated with
        # WHAM only known up to a constant (between ivnerse temperatures) factor.
        # So we test for (almost-)equality of ratios of partition functions.
        beta1 = 1.0
        beta2 = 1.0 / 3.0 ** 2
        est_Z1 = log_partition_function(self.dos, self.energies, beta1)
        est_Z2 = log_partition_function(self.dos, self.energies, beta2)
        true_Z1 = np.sqrt(2 * np.pi / beta1)
        true_Z2 = np.sqrt(2 * np.pi / beta2)

        self.assertAlmostEqual(np.exp(est_Z1) / np.exp(est_Z2), true_Z1 / true_Z2,
                               places=2)
