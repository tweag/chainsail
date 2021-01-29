import unittest

import numpy as np
from resaas.common.storage import AbstractStorageBackend
from resaas.common.spec import NaiveHMCParameters, ReplicaExchangeParameters, OptimizationParameters
from resaas.schedule_estimation.schedule_optimizers import SingleParameterScheduleOptimizer

from resaas.re_job_controller import AbstractREJobController, get_default_params

re_params = dict(num_replicas=8, num_optimization_samples=10,
                 num_production_samples=20, dump_interval=5)
ls_params = dict(timestep_adaption_limit=100)
opt_params = {
    "max_optimization_runs": 5,
    "target_value": 0.2,
    "max_param": 1.0,
    "min_param": 1.0,
    "decrement": 0.2,
}


class MockWham:
    def estimate_dos(self, energies, parameters):
        return len(parameters["beta"])


class MockOptimizer:
    def optimize(self, dos, energies):
        return {"beta": np.array([42] * (dos - 1))}


class MockRERunner:
    def run_sampling(self, storage):
        storage.save_final_timesteps(np.array([1, 2, 3]))
        cfg = storage.load_config()
        # save fake energies b/c I'm too stupid to mock
        # StorageWriter.load_all_energies()
        di = cfg["re"]["dump_interval"]
        for r in range(1, cfg["general"]["num_replicas"] + 1):
            for s in range(0, cfg["general"]["n_iterations"], di):
                storage.save_energies([1.0], "replica{}".format(r), s, s + di)


class MockREJobController(AbstractREJobController):
    def _write_hostsfile(self):
        pass

    def _scale_environment(self, _):
        pass


class MockStorageBackend(AbstractStorageBackend):
    def __init__(self):
        self._data = {}

    def write(self, data, filename, data_type):
        self._data[filename] = data

    def load(self, filename, data_type):
        return self._data[filename]


class testREJobController(unittest.TestCase):
    def setUp(self):
        optimizer = MockOptimizer()
        initial_schedule = {'beta': np.array([42] * 8)}
        self._controller = MockREJobController(
            1,
            "127.0.0.1",
            1234,
            re_params,
            ls_params,
            opt_params,
            MockRERunner(),
            MockStorageBackend(),
            optimizer,
            MockWham(),
            initial_schedule,
            basename="/tmp",
        )

    def testOptimizeSchedule(self):
        res_storage, res_sched = self._controller.optimize_schedule()
        res_dos = res_storage.load_dos()

        self.assertEqual(res_storage.sim_path, "optimization_run4")
        self.assertTrue(all(res_sched["beta"] == np.array([42] * 3)))
        self.assertEqual(res_dos, 4)
