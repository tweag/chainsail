Chainsail libraries:
- `runners`: runners are responsible for performing a single Replica Exchange simulation, given a fixed schedule, initial states, local MCMC sampler timesteps and other parameters.
- `schedule_estimation`: the code responsible for automatic determination of the inverse temperature schedule. Also contains a Weighted Histogram Analysis Method (WHAM) implementation which is used to estimate the density of states that is required for the schedule estimation.
- `grpc`: Google Remote Procedure Call (gRPC) specifications for controller health check and user code server.
- `common`: miscellaneous code shared between multiple Chainsail applications and libraries, such as the storage interface, the job specification, definition of tempered distributions, ...

See each library subdirectory for additional documentation.
