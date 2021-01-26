import numpy as np
import os, sys
from mpi4py import MPI

## communicators are classes which serve as an interface between, say, MPI and the rexfw code
## other communicators could use, e.g., the Python multiprocessing module to
## communicate between the master and the replicas
from rexfw.communicators.mpi import MPICommunicator

mpicomm = MPI.COMM_WORLD
rank = mpicomm.Get_rank()
size = mpicomm.Get_size()

n_replicas = size - 1

sim_name = 'normaltest'

## this is where all simulation output (samples, statistics files, etc.) are stored
output_folder = '/tmp/{}_{}replicas/'.format(sim_name, n_replicas)

comm = MPICommunicator()

if rank == 0:

    ## the first process (rank 0) runs an ExchangeMaster, which sends out 
    ## commands / requests to the replica processes, such as "sample", 
    ## "propose exchange states", "accept proposal", etc.

    from rexfw.convenience import setup_default_re_master, create_directories

    create_directories(output_folder)
    ## sets up a default RE master object; should be sufficient for all practical purposes
    master = setup_default_re_master(n_replicas, output_folder, comm)    
    master.run(10000,                    # number of MCMC samples
               swap_interval=5,          # interval of exchange attempts
               status_interval=50,       # interval with which to print / write out sampling statistics
               dump_interval=200,        # interval with which to dump samples to disk
               dump_step=3               # samples dump step: write out only every i-th sample
        )
    ## send kill request to break from infinite message receiving loop in replicas
    master.terminate_replicas()

else:

    ## every process with rank > 0 runs a replica, which does single-chain
    ## sampling and proposes exchange states

    from rexfw.convenience import setup_default_replica
    ## the slaves are relicts; originally I thought them to pass on
    ## messages from communicators to proposers / replicas, but now
    ## the replicas take care of everything themselves
    from rexfw.slaves import Slave
    ## a simple Metropolis-Hastings sampler...
    from rexfw.samplers.rwmc import RWMCSampler
    ## ... to sample from a normal distribution
    from rexfw.pdfs.normal import Normal

    pdf = Normal(sigma=float(rank))
    np.random.seed(rank)
    init_state = np.array([np.random.normal()])

    ## all additional parameters for the sampler go in this dict
    sampler_params = dict(stepsize=1.8, variable_name='x')
    replica = setup_default_replica(init_state, pdf, RWMCSampler, sampler_params,
                                    output_folder, comm, rank)
    slave = Slave({replica.name: replica}, comm)

    ## starts infinite loop in slave to listen for messages
    slave.listen()
