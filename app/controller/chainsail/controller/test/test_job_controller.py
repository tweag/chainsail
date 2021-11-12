import unittest
from unittest.mock import patch

import numpy as np
from chainsail.common.storage import AbstractStorageBackend
from chainsail.common.spec import (
    NaiveHMCParameters,
    ReplicaExchangeParameters,
    OptimizationParameters,
)
from chainsail.controller import BaseREJobController


def mock_setup_initial_states(current_storage, schedule, previous_storage):
    return np.array([0.01] * len(list(schedule.values())[0]))


class MockWham:
    def estimate_dos(self, energies, parameters):
        return len(parameters["beta"])


class MockOptimizer:
    def optimize(self, dos, energies):
        return {"beta": np.arange(dos - 1, 0, -1)}


class MockRERunner:
    def run_sampling(self, storage):
        sched = storage.load_schedule()
        # make nonsense stepsizes with same length as schedule
        mock_stepsizes = np.ones(len(list(sched.values())[0]))
        storage.save_final_stepsizes(mock_stepsizes)


class MockStorageBackend(AbstractStorageBackend):
    def __init__(self):
        self._data = {}

    def write(self, data, filename, data_type):
        self._data[filename] = data

    def load(self, filename, data_type):
        return self._data[filename]

    @property
    def file_not_found_exception(self):
        return ValueError


class testREJobController(unittest.TestCase):
    def setUp(self):
        initial_states_patcher = patch("chainsail.controller.setup_initial_states")
        initial_states_patcher.start()
        self.addCleanup(initial_states_patcher.stop)

        load_all_energies_patcher = patch(
            "chainsail.common.storage.SimulationStorage.load_all_energies", return_value=3
        )
        load_all_energies_patcher.start()
        self.addCleanup(load_all_energies_patcher.stop)

        optimizer = MockOptimizer()
        initial_schedule = {"beta": np.arange(7, 0, -1)}
        re_params = ReplicaExchangeParameters(
            num_optimization_samples=10, num_production_samples=20, dump_interval=5
        )
        opt_params = OptimizationParameters(max_optimization_runs=5)
        ls_params = NaiveHMCParameters()
        self._controller = BaseREJobController(
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
        self.assertTrue(np.all(res_sched["beta"] == np.arange(2, 0, -1)))
        self.assertEqual(res_dos, 3)
