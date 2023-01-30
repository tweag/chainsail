Chainsail applications:
- `client`: a React web app that provides the Chainsail website and wraps nicely around the scheduler's HTTP API for job submission and monitoring.
- `controller`: the algorithmic core of Chainsail, this app performs optimization simulations to figure out the correct inverse temperature schedule and finally launches a production run. Resorts to one of the runners in [`../lib/runners`](../lib/runners) for performing single Replica Exchange runs. Can be run stand-alone without any of the other applications.
- `scheduler`: Flask app that receives job specifications, creates new jobs, and instantiates new controllers. In short, it manages multiple, possibly parallel, Chainsail jobs.
- `mcmc_stats_server`: Flask app that reads energies (negative log-probabilities) and acceptance rates from Google Cloud storage and serves them to the client.
- `user_code_server`: a gRPC server that serves the user-defined log-probability, gradient and initial state and is meant to run inside the [`user_code` Docker container](../docker/user-code/) for encapsulation.

See each app's subdirectory for additional documentation.
Some of the applications are packaged in Docker images to be found in [`../docker/`](../docker/).
