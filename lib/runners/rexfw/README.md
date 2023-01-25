# `rexfw` runner

This is currently the only Replica Exchange implementation supported by Chainsail.
It is based on the `rexfw` library, which one of Chainsail's developers developed during his pre-Tweag research career.
The fork / branch used by Chainsail can be found [here](https://github.com/tweag/rexfw/tree/resaas).

## Requirements

As all Python code in Chainsail the `rexfw` runner is packaged using Poetry.
Python dependencies are thus listed in `pyproject.toml`.
Note that this runner has a crucial system dependency, namely a working Message Passing Interface (MPI) implemenation.
Chainsail itself uses OpenMPI (https://www.open-mpi.org/), but others might or might not work, too.

## Design

The `rexfw` runner implements the minimal `AbstractRERunner` interface from `/common/lib/runners/` in `./chainsail/runners/rexfw/__init__.py`.
This class runs a Python script `./chainsail/runners/rexfw/mpi.py` via `mpirun`, and the Python script (and the actual `rexfw` library) uses the `mpi4py` library to communicate between processes.
`rexfw` has a controller / worker architecture, in which one controller process distributes sampling / exchange / other tasks to one or several workers and thus orchestrates a Replica Exchange simulation.
Thanks to the use of MPI, the `rexfw` runner can be used on single machines as well as on a computing cluster or, as done in Chainsail's current full deployment, on a cluster of Kybernetes pods.
