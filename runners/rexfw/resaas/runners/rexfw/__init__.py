"""
Runners which launch a rexfw simulation.
"""

import os
from subprocess import check_output

from resaas.common.runners import AbstractRERunner, runner_config
from resaas.common.storage import AbstractStorageBackend


class MPIRERunner(AbstractRERunner):
    """
    Runs a rexfw sampler which uses openMPI for communication.
    """

    REXFW_SCRIPT = "run-rexfw-mpi"
    DEFAULT_HOSTSFILE = "hostsfile"
    DEFAULT_STORAGEFILE = "storage.yaml"

    def run_sampling(self, storage: AbstractStorageBackend):
        # Get configuration
        run_id = runner_config.get("run_id", default="no-id")
        hostsfile = runner_config.get("hostsfile", default=self.DEFAULT_HOSTSFILE)
        storage_config = runner_config.get("storage_config", default=self.DEFAULT_STORAGEFILE)

        model_config = storage.load_config()
        n_replicas = model_config["general"]["num_replicas"]
        cfg_path = os.path.join(
            storage.basename, storage.sim_path, storage.dir_structure.CONFIG_FILE_NAME
        )
        # Spawn an mpi subprocess
        cmd = [
            "mpirun",
            "--hostsfile",
            hostsfile,
            "--oversubscribe",
            "-n",
            f"{n_replicas + 1}",
            self.REXFW_SCRIPT,
            "--id",
            run_id,
            "--config",
            cfg_path,
            "--storage",
            storage_config,
        ]

        check_output(cmd)
