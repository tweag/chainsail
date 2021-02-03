"""
Runners which launch a rexfw simulation.
"""
<<<<<<< HEAD
import sys
import subprocess
import time
=======
import subprocess
>>>>>>> 33440dc... Redirect MPI subprocess stdout / stderr to controller process stdout

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
            "--name",
            run_id,
            "--storage",
            storage_config,
            "--basename",
            storage.basename,
            "--path",
            storage.sim_path,
        ]

        # run in subprocess, but capture both stdout and stderr and
        # redirect them to the parent's process stdout

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # https://stackoverflow.com/a/53830668/1656472
        while True:
            rd = process.stdout.readline()
            print(rd.decode("ascii"), end="")
            if not rd:  # EOF
                return_code = process.poll()
                if return_code is not None:
                    break
                time.sleep(0.1)  # cmd closed stdout, but not exited yet

        if return_code != 0:
            raise Exception(
                f"MPI subprocess exited with return code {return_code}")
