# Overview of algorithmic parameters
Running a Replica Exchange calculation and optimizing the schedule requires setting several parameters, which are listed here.
Parameters every user should think a little bit about and which are on the basic submission form are in boldface.

## Replica Exchange
Replica Exchange enhances sampling of a multimodal probability distribution `p(x)` by simulating not the distribution of interest, but also somehow "flatter", meaning easier-to-sample, versions of it and occasionally exchanging states between these otherwise independent simulations.
Accepting such a swap happens with a certain probability which is designed such that it maintains the equilibrium distributions of both participating simulations. 
The most important parameter is the choice of the flatter distributions.
We currently support a one-parameter family of distributions `p(x)^beta` with `0 < beta <= 1`.
For `beta=1`, we recover the distribution of interest, while for any other `beta`, we obtain a flatter version of `p(x)`.
The question is then how many flatter distributions of this family we should simulate and which `beta` values to choose, in short, how the "schedule" looks like.

### Iterative schedule optimization
Chainsail automatizes determination of the schedule by iteratively estimating increasingly better schedules from increasingly better Replica Exchange simulations.
After running a Replica Exchange simulation, its resulting samples are used to estimate an improved schedule.
That improved schedule is then used to run a better Replica Exchange simulation, the results of which can then be used to calculate an even better schedule and so on and so forth.
We refer to one such iteration as an `optimization super-iteration`.

#### Initial schedule
To set an initial schedule for the very first simulation, a few parameters are needed:
- **`beta_min`**: the minimum `beta` value occuring in the schedule; it defines the flattest distribution. Default: 0.01.
- **`beta_ratio`**: the automatic schedule optimization needs a schedule to start with. It is common practice to define a temperature schedule by a geometric progression in which the ratio of successive `beta` values is constant. The close `beta_ratio` is to one, the more gentle the the sequence of `beta`s progresses from one to zero. If you expect a lot of change in "sampling difficulty" close to `beta=1`, set this to close to 1 (say, 0.95), else, smaller values such as 0.5 might work. Default: 0.8.

#### Super-iteration parameters
The super-iteration loops runs a certain number of Replica Exchange simulations in sequence and terminates as soon as the number of replicas in the improved schedule doesn't change anymore or a maximum number `max_optimization_runs` is attained.
The parameters for schedule optimization are thus
- **`optimization_num_samples`**: number of samples to draw for each optimization run. Default: 5000.
- `optimization_max_runs`: maximum number of schedule optimization Replica Exchange runs to perform. Default: 3.
- `optimization_hmc_min_initial_time_step`: initial time step for the simulation of the target distribution. Default: 0.001
- `optimization_hmc_max_initial_time_step`: initial time step for the simulation of the flattest distribution. Default: 0.1


#### Density of states (DOS) estimation parameters
The key quantity required for calculating an improved schedule is the density of states (DOS).
It is estimated using a multiple histogram reweighting (WHAM) algorithm, which by itself has several parameters:
- `wham_burnin_fraction`: fraction of samples to discard as burnin. Default: 0.1
- `wham_samples_fraction`: fraction of Replica Exchange samples to use for WHAM. Too large values might lead to exhausting the controller node's memory. Default: 0.1. 
- `wham_max_iterations`: maximum number of WHAM iterations to perform. If sampling results are good, WHAM should converge quickly, say, within 1000 iterations. If it doesn't, the sampling is probably bad. Default: 5000.

#### Parameters for density of states-based schedule estimation
With the DOS at hand, an improved schedule is calculated.
This works by finding a sequence of `beta` values for which the acceptance rate is constant.
To that end, the algorithm starts at `beta=1` and decreases `beta` by a small steps of size `beta_decrement` until the target acceptance rate is predicted.
It then stores that value and starts afresh from it, finding the next `beta`. 
The parameters of this procedure are thus:
- `beta_decrement`: depending on how close you expect neighboring `beta`s to be, set this to a very small value (say, 0.0001) for closely-spaced `beta`s in the case of abrupt changes in "sampling difficulty" or wider apart (say, 0.01) for more well-behaved distributions. The smaller `beta_decrement`, the longer the optimization iteration takes. Default:  0.001.
- **`max_replicas`**: upper limit of temperatures to simulate. If the result of the schedule optimization exceeds this value, optimization is aborted and the current schedule is interpolated to fit the maximum number of allowed replicas. This number crucially determines the computational cost: the higher it is, the more processors and thus VMs are required. Default: 100.

### Other Replica Exchange parameters
Chainsail currently supports a single way of choosing exchange partners, namely, in an alternating manner, a simulation tries to exchange its state with its lower- or higher-temperature neighbor:
in the first round of exchanges, the exchange partners are given by the replicas with indice `(1,2), (3,4), (5,6),...` and then, after a certain number of samples, in the next round of exchanges, replicas with indices `(2,3), (4,5), (6,7)` attempt pairwise exchanges.
That way, optimal "communication" between all replicas is assured.
The only parameters here are
- `exchange_interval`: the interval in which an exchange is attempted. For a value of, say, 5, every 5th local sampling move is replaced by an exchange move. This value is shared between schedule optimization and production runs. Default : 5.
- **`num_production_samples`**: the number of samples to obtain in the production run. Default: 50000.



## Local sampling parameters
For local sampling, meaning sampling within a single replica, Chainsail currently supports only a naive implementation of Hamiltionian Monte Carlo (HMC) with a very simple heuristic for automatic timestep adaption.
The parameters are
- **`hmc_trajectory_length`**: length of the HMC trajectory. Default: 20
- `hmc_adaption_percentage`: upon acceptance / rejection, the HMC time step is increased / decreased by this percentage to eventually converge to an acceptance rate of 50%. Default: 0.95
- `hmc_num_adaption_steps`: length of burn-in after which adaption is stopped. Default: 10% of the number of total samples.

