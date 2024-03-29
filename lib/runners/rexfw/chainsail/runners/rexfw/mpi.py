"""
MPI-based rexfw runner script. Must be called from within an mpi context.
"""
import os
import logging
import sys

import click
import mpi4py.rc
import numpy as np
from mpi4py import MPI

from chainsail.common import import_from_user
from chainsail.common.storage import SimulationStorage, load_storage_config
from chainsail.common.tempering.tempered_distributions import BoltzmannTemperedDistribution
from chainsail.common.tempering.tempered_distributions import LikelihoodTemperedPosterior
from chainsail.common.samplers import get_sampler
from chainsail.common.spec import TemperedDistributionFamily
from chainsail.common.pdfs import SafeUserPDF
from chainsail.grpc import user_code_pb2


from rexfw.communicators.mpi import MPICommunicator
from rexfw.convenience import setup_default_re_master, setup_default_replica
from rexfw.slaves import Slave


logger = logging.getLogger(__name__)

# Disable finalization hook in global mpi4py config
mpi4py.rc.finalize = False

mpicomm = MPI.COMM_WORLD


# Define a custom hook which will **kill** all mpi processes on the
# first failure
# See https://stackoverflow.com/questions/49868333/fail-fast-with-mpi4py
def mpiabort_excepthook(exc_type, exc_value, exc_traceback):
    logger.error(
        "MPI process encountered an unchecked exception.",
        exc_info=(exc_type, exc_value, exc_traceback),
    )
    mpicomm.Abort(1)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def ensure_mpi_failure(func):
    def wrapper(*args, **kwargs):
        # Add the mpi abort hook
        sys.excepthook = mpiabort_excepthook
        func(*args, **kwargs)
        # If the program has not exited, continue on with the default hook
        sys.excepthook = sys.__excepthook__

    return wrapper


@click.command()
@click.option(
    "--dirname",
    required=True,
    type=str,
    help="Storage backend dirname",
)
@click.option(
    "--path",
    required=True,
    type=str,
    help="Subdirectory in which the storage backend should write data",
)
@click.option(
    "--storage",
    "storage_config",
    required=True,
    type=click.Path(exists=True),
    help="path to storage backend YAML config file",
)
@click.option(
    "--name",
    required=True,
    type=str,
    help="the name to use for tagging statistics metadata",
)
@click.option(
    "--metrics-host",
    required=True,
    type=str,
    help="the metrics logging host",
)
@click.option(
    "--metrics-port",
    required=True,
    type=int,
    help="the metrics logging port",
)
@click.option(
    "--user-code-host",
    required=True,
    type=str,
    help="the hostname for the user code gRPC server",
)
@click.option(
    "--user-code-port",
    required=True,
    type=int,
    help="the port for the user code gRPC server",
)
@ensure_mpi_failure
def run_rexfw_mpi(
    dirname,
    path,
    storage_config,
    name,
    metrics_host,
    metrics_port,
    user_code_host,
    user_code_port,
):
    rank = mpicomm.Get_rank()
    size = mpicomm.Get_size()

    # Number of replicas is inferred from the MPI environment
    n_replicas = size - 1

    # TODO: find better way to determine whether the runner is deployed locally
    # or on the cloud
    is_local_run = name.split(".")[0] == "job-1"

    if is_local_run:
        logging.debug("Attempting to load user-defined pdf and initial state")
        bare_pdf, init_state = import_from_user()
    else:
        logging.debug("Instantiating safe, wrapped user-defined PDF and getting initial state")
        job_id = int(name.split(".")[0][len("job") :])
        bare_pdf = SafeUserPDF(job_id, user_code_host, user_code_port)
        initial_state_bytes = bare_pdf.stub.InitialState(
            user_code_pb2.InitialStateRequest(job_id=job_id)
        ).initial_state_bytes
        init_state = np.frombuffer(initial_state_bytes)

    # this is where all simulation input data & output (samples, statistics files,
    # etc.) are stored
    storage_backend = load_storage_config(storage_config).get_storage_backend()
    storage = SimulationStorage(
        dirname=dirname,
        sim_path=path,
        storage_backend=storage_backend,
    )
    config = storage.load_config()

    comm = MPICommunicator()

    if rank == 0:
        # the first process (rank 0) runs an ExchangeMaster, which sends out
        # commands / requests to the replica processes, such as "sample",
        # "propose exchange states", "accept proposal", etc.

        # sets up a default RE master object; should be sufficient for all
        # practical purposes
        if is_local_run:
            graphite_params = None
        else:
            graphite_params = {
                "job_name": name,
                "graphite_url": metrics_host,
                "graphite_port": metrics_port,
            }
        master = setup_default_re_master(
            n_replicas,
            os.path.join(dirname, path),
            storage_backend,
            comm,
            graphite_params=graphite_params,
        )
        master.run(
            config["general"]["n_iterations"],
            config["re"]["swap_interval"],
            config["re"]["status_interval"],
            config["re"]["dump_interval"],
            0,  # replica id offset parameter, ignore this
            5,  # dump interval, which thins written samples
            config["re"]["statistics_update_interval"],
        )

        # write final stepsizes to simulation storage
        # The sampling statistics holds objects which internally keep a time
        # series of quantities such as the stepsize
        stepsize_quantities = filter(
            lambda x: x.name == "stepsize", master.sampling_statistics.elements
        )
        # Such a quantity x has a field "origins" which holds strings
        # identifying to which sampling objects this quantity is related.
        # Such a string is, in this case, "replicaXX", where XX enumerates
        # the replicas. We thus sort by the XXses to get the stepsizes
        # in the right order.
        sorted_stepsize_quantities = sorted(
            stepsize_quantities, key=lambda x: int(x.origins[0][len("replica") :])
        )
        storage.save_final_stepsizes(
            np.array([x.current_value for x in sorted_stepsize_quantities])
        )

        # send kill request to break from infinite message receiving loop in
        # replicas
        master.terminate_replicas()

    else:
        # every process with rank > 0 runs a replica, which does single-chain
        # sampling and proposes exchange states

        schedule = storage.load_schedule()

        # Turn user-defined pdf into a Boltzmann distribution
        if (
            dist_family := config["re"]["dist_family"]
        ) == TemperedDistributionFamily.BOLTZMANN.value:
            tempered_pdf = BoltzmannTemperedDistribution(bare_pdf, schedule["beta"][rank - 1])
        elif dist_family == TemperedDistributionFamily.LIKELIHOOD_TEMPERED.value:
            tempered_pdf = LikelihoodTemperedPosterior(bare_pdf, schedule["beta"][rank - 1])
        else:
            raise ValueError(f"Invalid tempered distribution family: '{dist_family}'")

        # If an initial state is already defined in the config, use that instead
        # of the user-specified one.
        if config["general"]["initial_states"] is not None:
            init_state = storage.load_initial_states()[rank - 1]

        if config["local_sampling"]["stepsizes"] is not None:
            stepsize = storage.load_initial_stepsizes()[rank - 1]
        else:
            stepsize = 0.1

        ls_params = config["local_sampling"]
        sampler = get_sampler(ls_params["sampler"])
        ls_params.pop("sampler")
        ls_params.pop("stepsizes")
        ls_params["stepsize"] = stepsize
        replica = setup_default_replica(
            init_state, tempered_pdf, sampler, ls_params, storage, comm, rank
        )

        # the slaves are relicts; originally I thought them to pass on
        # messages from communicators to proposers / replicas, but now
        # the replicas take care of everything themselves
        slave = Slave({replica.name: replica}, comm)

        # starts infinite loop in slave to listen for messages
        slave.listen()


if __name__ == "__main__":
    run_rexfw_mpi()
