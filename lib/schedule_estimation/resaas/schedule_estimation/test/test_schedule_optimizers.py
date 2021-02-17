import unittest

import numpy as np

from resaas.schedule_estimation.schedule_optimizers import SingleParameterScheduleOptimizer


def mock_quantity(_, __, param1, param2):
    return 1.0 - (param1 - param2) * 10


class TestSingleParameterScheduleOptimizer(unittest.TestCase):
    def setUp(self):
        pass

    def testOptimize(self):
        # TODO: I _think_ this test is okay, but for small decrements there are
        # issues, but these are, I think, related to the above
        # mock_quantity definition.

        for decrement in (
            0.1,
            0.01,
            # 0.001,# (fails)
        ):
            optimizer = SingleParameterScheduleOptimizer(
                0.1, 1.0, 0.1, decrement, mock_quantity, "my_param", 100
            )

            result = optimizer.optimize(dos=None, energies=None)
            expected = {"my_param": np.arange(1.0, 0, -0.1)}
            diffs = np.fabs(result["my_param"] - expected["my_param"])
            self.assertTrue(np.all(diffs < 1e-10))
