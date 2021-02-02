from io import BytesIO

import click
import numpy as np
import yaml
from mpi4py import MPI
from resaas.common.storage import SimulationStorage, load_storage_config

from rexfw.communicators.mpi import MPICommunicator
from rexfw.convenience import setup_default_re_master, setup_default_replica
from rexfw.pdfs.normal import Normal
from rexfw.samplers.rwmc import RWMCSampler
from rexfw.slaves import Slave


@click.command()
@click.option("--name", required=True, type=str, help="output directory name")
@click.option(
    "--basename",
    required=True,
    type=str,
    help="Storage backend basename",
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
def run_rexfw_mpi(name, basename, path, storage_config):
    mpicomm = MPI.COMM_WORLD
    rank = mpicomm.Get_rank()
    size = mpicomm.Get_size()

    # Number of replicas is inferred from the MPI environment
    n_replicas = size - 1

    # this is where all simulation input data & output (samples, statistics files,
    # etc.) are stored
    storage_backend = load_storage_config(storage_config).get_storage_backend()
    storage = SimulationStorage(
        basename=basename,
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
        master = setup_default_re_master(n_replicas, path, storage_backend, comm)
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

        if config["local_sampling"]["timesteps"] is not None:
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
