import unittest
import tempfile

import numpy as np
import yaml

from resaas.common.util import FileSystemStringStorage, FileSystemPickleStorage
from resaas.schedule_estimation.dos_estimators import WHAM, BoltzmannEnsemble
from resaas.schedule_estimation.schedule_optimizers import SingleParameterScheduleOptimizer
from .. import AbstractREJobController, FINAL_TIMESTEPS_PATH


class MockWham(WHAM):
    def estimate_dos(self):
        return len(self._parameters['beta'])


class MockOptimizer(SingleParameterScheduleOptimizer):
    def optimize(self, **args):
        return {'beta': np.array([42] * (self._dos - 1))}


class MockInitialScheduleMaker:
    def make_initial_schedule(self):
        return {'beta': np.array([42] * 8)}


class MockRERunner:
    def run_sampling(self, config_file, basename):
        pstorage = FileSystemPickleStorage(basename)
        sstorage = FileSystemStringStorage(basename)
        path = yaml.safe_load(
            sstorage.read(config_file))['general']['output_path']
        pstorage.write(np.array([1,2,3]), path + FINAL_TIMESTEPS_PATH)

class MockREJobController(AbstractREJobController):
    def _scale_environment(self, _):
        pass


class testREJobController(unittest.TestCase):
    def setUp(self):
        tempdir = tempfile.TemporaryDirectory()
        tempdir_name = tempdir.name
        self._tempdir_name = tempdir_name

        pstorage = FileSystemPickleStorage(tempdir_name)
        sstorage = FileSystemStringStorage(tempdir_name)

        re_params = dict(num_replicas=8, num_optimization_samples=5000,
                         dump_interval=1000)
        ls_params = dict(hmc_num_adaption_steps=100)
        job_spec = dict(re_params=re_params,
                        local_sampling_params=ls_params,
                        optimization_params={'max_optimization_runs': 5,
                                             'target_value': 0.2,
                                             'max_param': 1.0,
                                             'min_param': 1.0,
                                             'decrement': 0.2},
                        initial_schedule_params={},
                        path=tempdir_name)

        self._controller = MockREJobController(
            job_spec, MockRERunner(), pstorage, sstorage,
            MockInitialScheduleMaker, MockOptimizer,
            BoltzmannEnsemble, None, MockWham)

    def testOptimizeSchedule(self):
        res_path, res_sched, res_dos = self._controller.optimize_schedule()

        self.assertEqual(res_path, 'optimization_run4/')
        self.assertTrue(all(res_sched['beta'] == np.array([42] * 3)))
        self.assertEqual(res_dos, 4)
