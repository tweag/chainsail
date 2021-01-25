import unittest
from unittest import patch

import numpy as np
import tempfile

from resaas.common.util import FileSystemStringStorage, FileSystemPickleStorage
from resaas.schedule_estimation.dos_estimators import WHAM, BoltzmannEnsemble
from resaas.schedule_estimation.schedule_optimizers import SingleParameterScheduleOptimizer
from resaas.re_runners import AbstractRERunner
from resaas.re_job_controller import AbstractREJobController


class MockWham(WHAM):
    def estimate_dos(self):
        return len(self._params['beta'])


class MockOptimizer(SingleParameterScheduleOptimizer):
    def optimize(self):
        return {'beta': np.array([42] * (self._dos - 1))}


class MockInitialScheduleMaker:
    def make_initial_schedule(self, num_replicas, _, __):
        return {'beta': np.array([42] * 8)}


class MockRERunner(AbstractRERunner):
    def run_sampling(self, config_file, basename):
        # storage = FileSystemStringStorage(basename, 'w')
        # storage.write(None,
        pass


class MockREJobController(AbstractREJobController):
    def _scale_environment(self, _):
        pass


class testREJobController(unittest.TestCase):
    def setUp(self):
        tempdir = tempfile.TemporaryDirectory()
        tempdir_name = tempdir.name

        pstorage = FileSystemPickleStorage(tempdir_name)
        sstorage = FileSystemStringStorage(tempdir_name)

        re_params = dict(num_replicas=8, num_optimization_samples=5000)
        ls_params = dict(hmc_num_adaption_steps=100)
        job_spec = dict(re_params=re_params,
                        local_sampling_params=ls_params,
                        optimization_params={'max_optimization_runs': 5},
                        initial_schedule_params={},
                        path=tempdir_name)

        self._controller = MockREJobController(
            job_spec, MockRERunner(), pstorage, sstorage,
            MockInitialScheduleMaker, MockOptimizer,
            BoltzmannEnsemble, None, MockWham)

    @patch('resaas.re_job_controller.load_energies')
    def testOptimizeSchedule(self, load_energies_patch):
        load_energies_patch.return_value = None
        res_path, res_sched, res_dos = self._controller.optimize_schedule()

        self.assertEqual(res_path, self._tempdir + '/optimization_run5/')
        self.assertEqual(res_sched, {'beta': np.array([42] * 3)})
        self.assertEqual(res_dos, 3)
