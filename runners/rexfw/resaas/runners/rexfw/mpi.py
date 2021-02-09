"""
MPI-based rexfw runner script. Must be called from within an mpi context.
"""
import sys
from abc import ABC, abstractmethod

import click
import mpi4py.rc
import numpy as np
from mpi4py import MPI
from resaas.common.storage import SimulationStorage, load_storage_config

from rexfw.communicators.mpi import MPICommunicator
from rexfw.convenience import setup_default_re_master, setup_default_replica
from rexfw.pdfs import AbstractPDF
from rexfw.pdfs.normal import Normal
from rexfw.samplers.rwmc import RWMCSampler
from rexfw.slaves import Slave

# Disable finalization hook in global mpi4py config
mpi4py.rc.finalize = False

mpicomm = MPI.COMM_WORLD


# Define a custom hook which will **kill** all mpi processes on the
# first failure
# See https://stackoverflow.com/questions/49868333/fail-fast-with-mpi4py
def mpiabort_excepthook(type, value, traceback):
    print((type, value, traceback))
    mpicomm.Abort()
    sys.__excepthook__(type, value, traceback)


def ensure_mpi_failure(func):
    def wrapper(*args, **kwargs):
        # Add the mpi abort hook
        sys.excepthook = mpiabort_excepthook
        func(*args, **kwargs)
        # If the program has not exited, continue on with the default hook
        sys.excepthook = sys.__excepthook__

    return wrapper


class BoltzmannTemperedDistribution(AbstractPDF):
    """
    This wraps an object representing a probability density into a Boltzmann
    ensemble.

    For a physical system with potential energy E, the configurational part
    (meaning, independent from the momenta) of the Boltzmann distribution is
    given by q(E|beta) \propto exp(-beta * E). Here, beta is, up to a constant,
    the inverse temperature of the system of a heat bath the system is assumed
    to be coupled to. For any probability distribution p(x), we can define a
    pseudo-energy E(x) by E(x) = -log p(x). We can thus use the Boltzmann
    distribution to modify the "ruggedness" (height of modes) of p(x) via beta:
    for beta = 0; q(E(x)) becomes a uniform distribution, while for beta = 1,
    q(E(x)) = p(x). Intermediate beta values can thus be used to create a
    sequence of distributions that are increasingly easier to sample.
    """

    def __init__(self, pdf, beta=1.0):
        """
        Initalizes a Boltzmann distribution for a fake physical system defined
        by a probability density.

        Args:
            pdf(AbstractPdf): object representing a probability distribution
            beta(float): inverse temperature in the range 0 < beta <= 1
        """
        self.bare_pdf = pdf
        self.beta = beta

    def log_prob(self, x):
        """
        Log-probability of the Boltzmann distribution.

        Args:
            x: variate(s) of the underlying PDF
        """
        return self.beta * self.bare_pdf.log_prob(x)

    def gradient(self, x):
        """
        Gradient of the Boltzmann distribution's log-probability.

        Args:
            x: variate(s) of the underlying PDF
        """
        return self.beta * self.bare_pdf.gradient(x)

    def bare_log_prob(self, x):
        """
        Log-probability of the underlying probability density.

        This is required for multiple histogram reweighting.

        Args:
            x: variate(s) of the underlying PDF
        """
        return self.bare_pdf.log_prob(x)


@click.command()
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
@ensure_mpi_failure
def run_rexfw_mpi(basename, path, storage_config):
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

        # write final step sizes to simulation storage
        # The sampling statistics holds objects which internally keep a time
        # series of quantities such as the step size
        timestep_quantities = filter(
            lambda x: x.name == "stepsize", master.sampling_statistics.elements
        )
        # Such a quantity x has a field "origins" which holds strings
        # identifying to which sampling objects this quantity is related.
        # Such a string is, in this case, "replicaXX", where XX enumerates
        # the replicas. We thus sort by the XXses to get the time steps
        # in the right order.
        sorted_timestep_quantities = sorted(
            timestep_quantities, key=lambda x: int(x.origins[0][len("replica") :])
        )
        storage.save_final_timesteps(
            np.array([x.current_value for x in sorted_timestep_quantities])
        )

        # send kill request to break from infinite message receiving loop in
        # replicas
        master.terminate_replicas()

    else:
        # every process with rank > 0 runs a replica, which does single-chain
        # sampling and proposes exchange states

        schedule = storage.load_schedule()

        # For now, we sample from a normal distribution, but here would eventually
        # be the user code imported
        bare_pdf = Normal()

        # Turn it into a Boltzmann distribution
        tempered_pdf = BoltzmannTemperedDistribution(bare_pdf, schedule["beta"][rank - 1])

        # TODO: this is currently a bit annoying: we don't know the number of
        # variables. Either the user provides it in the pdf object or they have to
        # provide initial states, which might not be a bad idea, actually.
        tempered_pdf.n_variables = 1
        if config["general"]["initial_states"] is None:
            init_state = np.random.normal(size=(tempered_pdf.n_variables,))
        else:
            init_state = storage.load_initial_states()[rank - 1]

        if config["local_sampling"]["timesteps"] is not None:
            timestep = storage.load_initial_timesteps()[rank - 1]
        else:
            timestep = 1

        # We use a simple Metropolis-Hastings sampler
        ls_params = config['local_sampling']
        sampler_params = {
            "stepsize": timestep,
            "timestep_adaption_limit": ls_params['timestep_adaption_limit'],
            "adaption_uprate": ls_params['adaption_uprate'],
            "adaption_downrate": ls_params['adaption_downrate']
        }
        replica = setup_default_replica(
            init_state, tempered_pdf, RWMCSampler, sampler_params, storage, comm, rank
        )

        # the slaves are relicts; originally I thought them to pass on
        # messages from communicators to proposers / replicas, but now
        # the replicas take care of everything themselves
        slave = Slave({replica.name: replica}, comm)

        # starts infinite loop in slave to listen for messages
        slave.listen()


if __name__ == "__main__":
    run_rexfw_mpi()
