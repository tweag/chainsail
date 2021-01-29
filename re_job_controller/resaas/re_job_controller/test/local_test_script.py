import pathlib
import os

from resaas.re_job_controller import (
    LocalREJobController,
    get_default_params,
    make_geometric_schedule)
from resaas.re_job_controller.initial_schedules import make_geometric_schedule
from resaas.re_runners import MPIRERunner
from resaas.schedule_estimation.dos_estimators import WHAM, BoltzmannEnsemble
from resaas.schedule_estimation.optimization_quantities import acceptance_rate
from resaas.schedule_estimation.schedule_optimizers import SingleParameterScheduleOptimizer
from resaas.common.storage import SimulationStorage, LocalStorageBackend


class HackedMPIRERunner:
    # TODO: refactor MPIRERunner to allow for easy monkey-patching
    def __init__(self, rexfw_path):
        self._rexfw_path = os.path.join(rexfw_path, '')

    def run_sampling(self, storage):
        config = storage.load_config()
        n_replicas = config["general"]["num_replicas"]
        cfg_path = os.path.join(
            storage.basename, storage.sim_path, storage.dir_structure.CONFIG_FILE_NAME
        )
        mpirun_args = ["--oversubscribe", "-n", str(n_replicas + 1)]
        run_script_args = [cfg_path, "local"]
        current_dir = pathlib.Path(__file__).parent.absolute()
        check_output(
            ["mpirun"] + mpirun_args
            + [os.path.join(current_dir, "launch_rexfw.sh"), self._rexfw_path]
            + run_script_args
        )


optimizer = SingleParameterScheduleOptimizer(
    target_value=0.8, max_param=1.0, min_param=0.01, decrement=0.01,
    optimization_quantity=acceptance_rate, param_name='beta')
wham = WHAM(BoltzmannEnsemble())
initial_schedule = make_geometric_schedule(
    'beta', num_replicas=10, min_value=0.1)
storage_backend = LocalStorageBackend()
runner = HackedMPIRERunner('/home/simeon/projects/tweag/rexfw/')
controller = LocalREJobController(
    42, '127.0.0.1', 1234,
    *get_default_params(),
    runner, storage_backend,
    optimizer, wham,
    initial_schedule,
    basename='/tmp/testsimulation')

controller.run_job()
