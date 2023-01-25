# Replica Exchange runners

Runners are responsible for executing a single Replica Exchange simulation with a fixed schedule and set of configuration parameters.

## Interface

Runners have a very simple interface defined in `/lib/common/chainsail/common/runners.py`.
It consists of a method `run_sampling` that takes a `SimulationStorage` object defined in `/lib/common/chainsail/common/storage.py`.
`run_sampling` is called by the controller application (`/app/controller/`).
All runner implementations consume configuration, initial Markov chain states, timesteps etc. and write sampling data exclusively via the storage backend provided to `run_sampling`.
