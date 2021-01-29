"""
Runners which launch a rexfw simulation in different deployments.
"""

import os
from subprocess import check_output

from resaas.common.runners import AbstractRERunner
from resaas.common.storage import AbstractStorageBackend


class MPIRERunner(AbstractRERunner):
    """
    Runs a rexfw sampler which uses openMPI for communication.

    This runner uses an openmpi hostsfile which by default
    is expected to exist in $PWD/hostsfile. The path to the
    hostsfile may be configured using the 'HOSTSFILE' environment
    variable.

    Args:
        hostsfile: The path to the openMPI hostsfile
    """

    REXFW_SCRIPT = "resaas.runners.rexfw.mpi"

    DEFAULT_HOSTSFILE = "hostsfile"
    HOSTSFILE_ENV_VAR = "HOSTSFILE"

    def run_sampling(self, storage: AbstractStorageBackend):
        hostsfile = os.environ.get(self.HOSTSFILE_ENV_VAR, default=self.DEFAULT_HOSTSFILE)
        config = storage.load_config()
        n_replicas = config["general"]["num_replicas"]
        cfg_path = os.path.join(
            storage.basename, storage.sim_path, storage.dir_structure.CONFIG_FILE_NAME
        )
        cmd = [
            "mpirun",
            "--hostsfile",
            hostsfile,
            "--oversubscribe",
            "-n",
            str(n_replicas + 1),
            "python",
            "-m",
            self.REXFW_SCRIPT,
            cfg_path,
            # TODO: Select storage based on input
            "local",
        ]

        check_output(cmd)
