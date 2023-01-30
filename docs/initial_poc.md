# Sketch of the initial proof-of-concept

For now, we are only considering the back-end. Front-end can be added later and will communicate with the back-end using a REST API.

## Recap: what is this service good for
This service allows users to sample high-dimensional, multimodal probability distributions via a combination of "local" sampling (via, most certainly, HMC or a variant) and "global" sampling (via a Replica Exchange (RE) algorithm).
After a user submits a sampling problem, the service will then do several preliminary sampling runs and automatically tune parameters such as number of replicas, the temperature schedule etc. via histogram reweighting and the density of states.
Once this optimization is finished, a production run is performed.
After the production run is done, the user gets a link to a cloud bucket, which contains the samples, sampling statistics such as acceptance rates and an estimate of the density of states.

## Components of this service
We have a sketch of the components available [here](/images/service_architecture.png).

### Replica Exchange implementation
At the heart of this initial proof-of-concept is a [Replica Exchange (RE) implementation](https://github.com/simeoncarstens/rexfw/tree/py3) Simeon wrote for his research back then. We have [forked this project](https://github.com/tweag/rexfw/tree/resaas) in the Tweag org for the development of Chainsail.
It uses the Message Passing Interface (MPI) to communicate between one (unfortunately still badly named) master process and several slave processes, each of which is responsible for local sampling of a single replica.
It should be easily possible to extend this implementation to means of communication between replicas other than MPI.

### Scheduler
The scheduler takes care of
- controlling (starting / stopping) new sampling jobs on request of the user
- scaling up or down the computing environment on request of the JobController
It exposes a REST API for submitting new job requests and interacting with jobs. It also exposes a backend endpoint via which job controllers can request resizing of their job cluster.

### Job controller
The controller takes care of
- calculating new RE parameters (schedule, number of replicas, initial states) from previous preliminary sampling runs,
- requesting an up- or downscaling of the computing environment (depenging on these new parameters) from the Scheduler
- kicking off the next sampling run with these new parameters in the adjusted environment,
It loops over these three points (in that order) until some convergence / stopping criterion is met and finally initiates a production run instead of another iteration of this loop. It should also store sampling run results in a (TODO: which?) database.

### Replica Exchange Job Runner
The Replica Exchange job runner launches a new `rexfw` calculation. It takes as inputs
- the algorithmic parameters (initial states, timesteps, temperature schedule)
- output settings (where to store samples)
- a REJobId / iteration ID / something else that identifies the sampling statistics logged to the Metadata server as belonging to this particular iteration
- a definition of the computing environment

### Job database
The job database has one entry for each sampling run and stores its metadata:
- User-supplied job specs
  - Initial replica Exchange / local sampling parameters (temperature schedule, timesteps),
- Node metadata
- where to find sampling results.

### Controller
Main entrypoint of a single job. This process runs a monitoring server to which the scheduler can connect and handles executing the ModelRunner. The ModelRunner is an object which executes rexfw code and performs parameter tuning.

### MetaServer
Mini flask server with endpoints for logging sampling data. Replicas and master processes can use this to log metadata while sampling.

### Meta DB
Database backend for sampling metadata


## Complete workflow
Here's how the life of one sampling job would look like:
1. user submits job to the scheduler
1. scheduler uses configured job generation methods to:
   1. Create new compute resources (e.g. VMs), "Nodes"
   1. Provision those nodes with required dependencies
   1. Start entrypoints on each node
   1. Start monitoring via the job controller endpoint
1. Controller begins run by calling configured ModelRunner after being started by the scheduler
   1. As an example, we can consider an MPI-based model runner
   1. Runner runs one iteration of sampling
   1. Runner adjusts sampling parameters:
      1. Uses histogram to get density of states estimate (DOS)
      1. Uses DOS to calculate new temperature schedule
      1. Uses DOS to calculate new initial states
      1. Optionally submits request for additional compute resources to scheduler via the controller
   1. Repeat the above steps until optimal parameters are found.
   1. Runner performs final, "production" sampling run
   1. Runner performs post-processing, calculating final DOS estimate
   1. Runner exits, returning exit status and final metadata (as applicable) to the scheduler via the controller
1. When exit signal from controller is received, scheduler updates job status and notifies user. It can then begin tearing down the job cluster.
1. User downloads results
