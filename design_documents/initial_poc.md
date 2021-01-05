# Sketch of the initial proof-of-concept

For now, we are only considering the back-end. Front-end can be added later and will communicate with the back-end using a REST API.

## Recap: what is this service good for
This service allows users to sample high-dimensional, multimodal probability distributions via a combination of "local" sampling (via, most certainly, HMC or a variant) and "global" sampling (via a Replica Exchange (RE) algorithm).
After a user submits a sampling problem, the service will then do several preliminary sampling runs and automatically tune parameters such as number of replicas, the temperature schedule etc. via histogram reweighting and the density of states.
Once this optimization is finished, a production run is performed.
After the production run is done, the user gets a link to a cloud bucket, which contains the samples, sampling statistics such as acceptance rates and an estimate of the density of states. 

## Components of this service
For now, we only have a very rough graphical sketch of the components available [here](https://docs.google.com/document/d/1DcTozCzTmUbJbhQtj-tYSYvWHRpI2I_mOWS19BOutlk/edit?ts=5ff44579).
### Replica Exchange implementation
At the heart of this initial proof-of-concept is a [Replica Exchange (RE) implementation](https://github.com/simeoncarstens/rexfw/tree/py3) Simeon wrote for his research back then.
It uses the Message Passing Interface (MPI) to communicate between one (unfortunately still badly named) master process and several slave processes, each of which is responsible for local sampling of a single replica.
It should be easily possible to extend this implementation to means of communication between replicas other than MPI.

### Scheduler
The scheduler takes care of
- calculating new RE parameters (schedule, number of replicas, initial states) from previous preliminary sampling runs,
- scaling up / down the computing environment (single big machine or a cluster) according to these new parameters,
- initiating the next sampling run with these new parameters in the adjusted environment,
- looping over the previous three points (in that order) until some convergence / stopping criterion is met and finally runs a production run instead of another iteration of this loop,
- storing sampling run results in the job database.

### Job database
The job database has one entry for each sampling run and stores its metadata:
- Replica Exchange / local sampling parameters (temperature schedule, timesteps),
- environment parameters (cluster size),
- diagnostics values such as acceptance rates,
- where to find initial states,
- where to find sampling results.

### API
We will probably want to have a language-agnostic API through which the user can
- submit a sampling job, 
- talk to the scheduler to possibly manually intervene (change parameters or abort job),
- retrieve the results.

## Complete workflow
Here's how the life of one sampling job would look like:
1. user submits job via the API
2. scheduler determines initial schedule and computing environment from info contained in the submitted job data
3. scheduler sets up computing environment
4. scheduler initiates preliminary run
5. MPI-based RE implementation performs sampling
6. scheduler interrupts RE sampling after a fixed number of samples or after some other criterion is met
7. scheduler saves run metadata in job database
8. scheduler uses histogram reweighting to get an estimate of the density of states (DOS)
9. scheduler uses DOS to calculate a better temperature schedule
10. scheduler uses DOS to calculate new initial states
11. scheduler adjusts computing environment to new temperature schedule
12. scheduler starts again at 4.) and loops until some convergence criterium for the schedule is met
13. scheduler initiates long production sampling run
14. MPI-based RE implementation samples for a long time (possibly user-defined)
15. scheduler calculates final estimate of DOS
16. scheduler saves production run metadata to data base
17. scheduler notifies user that sampling is finished
18. user downloads results and inspects them
19. if user is happy with results, data on cloud buckets can be cleaned up
