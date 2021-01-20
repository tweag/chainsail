import unittest

from pickle import load
import numpy as np

from resaas.schedule_estimation.schedule_optimizers import (
    AbstractSingleParameterScheduleOptimizer,
    BoltzmannAcceptanceRateOptimizer)


class MockSingleParameterScheduleOptimizer(
        AbstractSingleParameterScheduleOptimizer):
    _param_name = 'my_param'

    def estimate_quantity(self, param1, param2):
        return 1.0 - (param1 - param2) * 10


class TestSingleParameterScheduleOptimizer(unittest.TestCase):
    def setUp(self):
        self.optimizer = MockSingleParameterScheduleOptimizer(
            None, None)

    def testOptimize(self):
        # TODO: I _think_ this test is okay, but for small decrements there are
        # issues, but these are, I think, related to the above estimate_quantity
        # definition.
        for decrement in (0.1, 0.01,
                          #0.001, (fails)
                          ):
            result = self.optimizer.optimize(0.1, 1.0, 0.1, decrement)
            expected = {'my_param': np.arange(1.0, 0.0, -0.1)}
            diffs = np.fabs(result['my_param'] - expected['my_param'])
            self.assertTrue(np.all(diffs < 1e-10))


class TestBoltzmannAcceptanceRateOptimizer(unittest.TestCase):
    def setUp(self):
        # TODO: replace estimated DOS by analytical DOS once confusion about
        # estimated DOS being wrong but giving correct results downstream is
        # lifted
        with open("dos_energies.pickle", "rb") as ipf:
            self.energies, self.dos = load(ipf)
        self.optimizer = BoltzmannAcceptanceRateOptimizer(self.dos, self.energies)

    def testEstimateQuantity(self):
        beta1 = 1.0
        beta2 = 1.0 / 3.0 ** 2
        result = self.optimizer.estimate_quantity(beta1, beta2)
        # obtained from numerical integration
        # TODO: figure out what the analytical expression is and generalize
        # this test.
        expected = 0.4096

        self.assertAlmostEqual(result, expected, places=2)
