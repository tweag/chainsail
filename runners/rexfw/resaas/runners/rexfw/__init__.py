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
        run_id = runner_config.get("run_id", "no-id")
        hostsfile = runner_config.get("hostsfile", self.DEFAULT_HOSTSFILE)
        storage_config = runner_config.get("storage_config", self.DEFAULT_STORAGEFILE)

        model_config = storage.load_config()
        n_replicas = model_config["general"]["num_replicas"]

        PATH = os.environ["PATH"]
        PYTHONPATH = os.environ["PYTHONPATH"]
        # Spawn an mpi subprocess
        cmd = [
            "mpirun",
            # For running in docker
            "--allow-run-as-root",
            "--hostfile",
            hostsfile,
            "--oversubscribe",
            "-n",
            f"{n_replicas + 1}",
            # Note: ssh will by default wipe the environment variables when
            # entering remote nodes if they are running in a container. To handle
            # these cases we explicitely send the PATH and PYTHONPATH variables from the
            # controller.
            # "--mca",
            # "mca_base_env_list",
            # f"PATH='{PATH}',PYTHONPATH='{PYTHONPATH}'",
            self.REXFW_SCRIPT,
            "--storage",
            storage_config,
            "--basename",
            f"{storage.basename}/{run_id}",
            "--path",
            storage.sim_path,
        ]

        check_output(cmd)
