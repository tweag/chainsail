"""
Runners which launch a rexfw simulation.
"""
import logging
import subprocess
import time

from resaas.common.runners import AbstractRERunner, runner_config
from resaas.common.storage import AbstractStorageBackend

logger = logging.getLogger(__name__)


class MPIRERunner(AbstractRERunner):
    """
    Runs a rexfw sampler which uses openMPI for communication.
    """

    REXFW_SCRIPT = "run-rexfw-mpi"
    DEFAULT_HOSTSFILE = "hostsfile"
    DEFAULT_STORAGEFILE = "storage.yaml"

    def run_sampling(self, storage: AbstractStorageBackend):
        # Get configuration
        hostsfile = runner_config.get("hostsfile", self.DEFAULT_HOSTSFILE)
        storage_config = runner_config.get("storage_config", self.DEFAULT_STORAGEFILE)

        model_config = storage.load_config()
        n_replicas = model_config["general"]["num_replicas"]

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
            self.REXFW_SCRIPT,
            "--storage",
            storage_config,
            "--basename",
            f"{storage.basename}",
            "--path",
            storage.sim_path,
        ]

        logger.debug(f"Calling mpirun with: {cmd}")
        # run in subprocess, but capture both stdout and stderr and
        # redirect them to the parent's process stdout
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # https://stackoverflow.com/a/53830668/1656472
        while True:
            rd = process.stdout.readline()
            logger.info(rd.decode("ascii"))
            if not rd:  # EOF
                return_code = process.poll()
                if return_code is not None:
                    break
                time.sleep(0.1)  # cmd closed stdout, but not exited yet

        if return_code != 0:
            raise Exception(f"MPI subprocess exited with return code {return_code}")
