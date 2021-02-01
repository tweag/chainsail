"""
Runners which launch a rexfw simulation.
"""

import os
from subprocess import check_output

from resaas.common.runners import AbstractRERunner, runner_config
from resaas.common.storage import SimulationStorage


class BaseMPIRERunner(AbstractRERunner):
    """
    Runs a rexfw sampler which uses openMPI for communication and which can
    run locally.
    """

    REXFW_SCRIPT = "run-rexfw-mpi"
    DEFAULT_STORAGEFILE = "storage.yaml"

    def _mpirun_args(self, n_replicas):
        return ["--oversubscribe",
                "-n",
                f"{n_replicas + 1}"]

    def run_sampling(self, storage: SimulationStorage):
        # Get configuration
        run_id = runner_config.get("run_id", default="no-id")
        storage_config = runner_config.get("storage_config", default=self.DEFAULT_STORAGEFILE)

        model_config = storage.load_config()
        n_replicas = model_config["general"]["num_replicas"]
        cfg_path = os.path.join(
            storage.basename, storage.sim_path, storage.dir_structure.CONFIG_FILE_NAME
        )
        # Spawn an mpi subprocess
        cmd = [
            "mpirun",
            *self._mpirun_args(n_replicas),
            self.REXFW_SCRIPT,
            "--id",
            run_id,
            "--config",
            cfg_path,
            "--storage",
            storage_config,
        ]

        check_output(cmd)


class CloudMPIRERunner(AbstractRERunner):
    """
    Runs a rexfw sampler which uses openMPI for communication.
    """

    DEFAULT_HOSTSFILE = "hostsfile"

    def _mpirun_args(self, n_replicas):
        hostfile = runner_config.get("hostsfile", default=self.DEFAULT_HOSTSFILE)
        return super()._mpirun_args(n_replicas) + ["--hostsfile", hostfile]
