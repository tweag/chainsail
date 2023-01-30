"""
Runners which launch a rexfw simulation.
"""
import logging
import subprocess
import time

from chainsail.common.runners import AbstractRERunner, runner_config
from chainsail.common.storage import SimulationStorage

logger = logging.getLogger("chainsail.controller")


def format_metric_name(run_id: int, storage: SimulationStorage):
    return f"job{run_id}.{storage.sim_path}"


class MPIRERunner(AbstractRERunner):
    """
    Runs a rexfw sampler which uses openMPI for communication.
    """

    REXFW_SCRIPT = "run-rexfw-mpi"
    DEFAULT_RUN_ID = 1
    DEFAULT_HOSTFILE = "hostfile"
    DEFAULT_STORAGEFILE = "storage.yaml"
    DEFAULT_METRICS_HOST = "localhost"
    DEFAULT_METRICS_PORT = 2004
    DEFAULT_USER_CODE_HOST = "localhost"
    DEFAULT_USER_CODE_PORT = 50052

    def run_sampling(self, storage: SimulationStorage):
        # Get configuration
        hostfile = runner_config.get("hostfile", self.DEFAULT_HOSTFILE)
        storage_config = runner_config.get("storage_config", self.DEFAULT_STORAGEFILE)
        run_id = runner_config.get("run_id", self.DEFAULT_RUN_ID)
        metrics_host = runner_config.get("metrics_host", self.DEFAULT_METRICS_HOST)
        metrics_port = runner_config.get("metrics_port", self.DEFAULT_METRICS_PORT)
        user_code_host = runner_config.get("user_code_host", self.DEFAULT_USER_CODE_HOST)
        user_code_port = runner_config.get("user_code_port", self.DEFAULT_USER_CODE_PORT)

        model_config = storage.load_config()
        n_replicas = model_config["general"]["num_replicas"]

        name = format_metric_name(run_id, storage)

        # Spawn an mpi subprocess
        cmd = [
            "mpirun",
            # For running in docker
            "--allow-run-as-root",
            "--hostfile",
            hostfile,
            # "--oversubscribe",
            "-n",
            f"{n_replicas + 1}",
            self.REXFW_SCRIPT,
            "--storage",
            storage_config,
            "--dirname",
            storage.dirname,
            "--path",
            storage.sim_path,
            "--name",
            name,
            "--metrics-host",
            metrics_host,
            "--metrics-port",
            str(metrics_port),
            "--user-code-host",
            user_code_host,
            "--user-code-port",
            str(user_code_port),
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
