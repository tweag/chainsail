import sys
import os
from io import BytesIO

import yaml

import numpy as np
from mpi4py import MPI

from resaas.common.storage import SimulationStorage, LocalStorageBackend, CloudStorageBackend

from rexfw.convenience import setup_default_re_master
from rexfw.convenience import setup_default_replica
from rexfw.slaves import Slave
from rexfw.samplers.rwmc import RWMCSampler
from rexfw.pdfs.normal import Normal
from rexfw.communicators.mpi import MPICommunicator

# TODO: This function needs to accept inputs for configuring the storage backend


def run_rexfw_mpi():
    # communicators are classes which serve as an interface between, say, MPI
    # and the rexfw code  other communicators could use, e.g., the Python
    # multiprocessing module to communicate between the master and the replicas

    # TODO: getting the number of replicas (and that's all the MPI stuff here is
    # for) should rather be a task of the communicator.
    mpicomm = MPI.COMM_WORLD
    rank = mpicomm.Get_rank()
    size = mpicomm.Get_size()
    n_replicas = size - 1

    config_file = sys.argv[1]
    with open(config_file) as ipf:
        config = yaml.safe_load(ipf.read())
    # TODO: using a command line argument, we can set whether cloud or file system
    # storage should be used
    env = sys.argv[2]

    # this is where all simulation input data & output (samples, statistics files,
    # etc.) are stored
    basename = config["general"]["basename"]
    output_folder = config["general"]["output_path"]
    # TODO: make statistics writing use RESAAS storage
    abs_output_folder = os.path.join(basename, output_folder)
    if env == "local":
        storage_backend = LocalStorageBackend()
    elif env == "cloud":
        # TODO: needs libcloud driver and container
        storage_backend = CloudStorageBackend()
    storage = SimulationStorage(basename, output_folder, storage_backend)

    for stats_folder in ("statistics", "works", "heats"):
        os.makedirs(os.path.join(abs_output_folder, stats_folder), exist_ok=True)

    comm = MPICommunicator()

    if rank == 0:
        # the first process (rank 0) runs an ExchangeMaster, which sends out
        # commands / requests to the replica processes, such as "sample",
        # "propose exchange states", "accept proposal", etc.

        # sets up a default RE master object; should be sufficient for all
        # practical purposes
        master = setup_default_re_master(n_replicas, abs_output_folder, comm)
        master.run(
            config["general"]["n_iterations"],
            config["re"]["swap_interval"],
            config["re"]["status_interval"],
            config["re"]["dump_interval"],
            0,  # replica id offset parameter, ignore this
            5,  # dump interval, which thins written samples
            config["re"]["statistics_update_interval"],
        )

        # copy over final step sizes
        mcmc_stats_path = "statistics/mcmc_stats.txt"
        mcmc_stats_buffer = storage.load(mcmc_stats_path, data_type="text")
        timesteps = np.loadtxt(BytesIO(bytes(mcmc_stats_buffer, "ascii")), dtype=float)[-1, 2::2]
        storage.save_final_timesteps(timesteps)

        # send kill request to break from infinite message receiving loop in
        # replicas
        master.terminate_replicas()

    else:
        # every process with rank > 0 runs a replica, which does single-chain
        # sampling and proposes exchange states

        schedule = storage.load_schedule()

        # For now, we sample from a normal distribution, but here would eventually
        # be the user code imported
        pdf = Normal(sigma=1 / np.sqrt(schedule["beta"][rank - 1]))

        # TODO: this is currently a bit annoying: we don't know the number of
        # variables. Either the user provides it in the pdf object or they have to
        # provide initial states, which might not be a bad idea, actually.
        pdf.n_variables = 1
        if config["general"]["initial_states"] is None:
            init_state = np.random.normal(pdf.n_variables)
        else:
            init_state = storage.load_initial_states()[rank - 1]

        if timesteps_path := config["local_sampling"]["timesteps"] is not None:
            timestep = storage.load_initial_timesteps()[rank - 1]
        else:
            timestep = 1

        # We use a simple Metropolis-Hastings sampler with its only parameter
        # being the step size
        sampler_params = {"stepsize": timestep}
        replica = setup_default_replica(
            init_state, pdf, RWMCSampler, sampler_params, storage, comm, rank
        )

        # the slaves are relicts; originally I thought them to pass on
        # messages from communicators to proposers / replicas, but now
        # the replicas take care of everything themselves
        slave = Slave({replica.name: replica}, comm)

        # starts infinite loop in slave to listen for messages
        slave.listen()


if __name__ == "__main__":
    run_rexfw_mpi()
