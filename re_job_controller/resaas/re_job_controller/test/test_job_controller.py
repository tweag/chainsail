import unittest

import numpy as np
import yaml

from resaas.common.storage import SimulationStorage, AbstractStorageBackend, dir_structure
from resaas.schedule_estimation.schedule_optimizers import SingleParameterScheduleOptimizer
from resaas.re_job_controller import AbstractREJobController


class MockWham:
    def estimate_dos(self, energies, parameters):
        return len(parameters['beta'])


class MockOptimizer(SingleParameterScheduleOptimizer):
    def optimize(self, dos, energies):
        return {'beta': np.array([42] * (dos - 1))}


class MockInitialScheduleMaker:
    def make_initial_schedule(self):
        return {'beta': np.array([42] * 8)}


class MockRERunner:
    def run_sampling(self, storage):
        storage.write(np.array([1, 2, 3]),
                      dir_structure.FINAL_TIMESTEPS_PATH)


class MockREJobController(AbstractREJobController):
    def _scale_environment(self, _):
        pass


class MockStorageBackend(AbstractStorageBackend):
    def __init__(self):
        self._data = {}
        
    def write(self, data,  filename):
        self._data[filename] = data

    def read(self, filename, data_type):
        return self._data[filename]


class testREJobController(unittest.TestCase):
    def setUp(self):
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
                        initial_schedule_params={})

        opt_params_copy = job_spec['optimization_params'].copy()
        opt_params_copy.pop('max_optimization_runs')
        optimizer = MockOptimizer(optimization_quantity=None,
                                  param_name='beta', **opt_params_copy)
        self._controller = MockREJobController(
            job_spec, MockRERunner(), MockStorageBackend(), optimizer,
            MockWham(), MockInitialScheduleMaker())

    def testOptimizeSchedule(self):
        res_path, res_sched, res_dos = self._controller.optimize_schedule()

        self.assertEqual(res_path, 'optimization_run4/')
        self.assertTrue(all(res_sched['beta'] == np.array([42] * 3)))
        self.assertEqual(res_dos, 4)
