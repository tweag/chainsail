# Optimization of Replica Exchange schedules via the density of states
The automatic optimization of temperature schedules for Replica Exchange is one of the main features of Chainsail.
A technical explanation is [available in the docs](../../docs/density_of_states_methods.pdf).
The basic idea is that one can combine samples from all temperatures in a Replica Exchange simulation using a method called [Weighted Histogram Analysis Method (WHAM)](https://www.semanticscholar.org/paper/Evaluation-of-marginal-likelihoods-via-the-density-Habeck/bbfdb49fa8fc31088d7514a6b684dec8230e4d6a) to obtain good estimate of a quantity called the [density of states (DOS)](https://en.wikipedia.org/wiki/Density_of_states).
Knowledge of this quantity allows relatively easy calculate a wide range of expectation values with respect to the probability distribution of interest.
In particular, it allows the estimation of the expected acceptance rate between two replicas with different values for the tempering parameter (currently, the "inverse temperature" `beta`).
This is exploited to find a sequence of parameter values for neighboring values of which the expected acceptance rate is some reasonable constant, say, 20%.
This sequence is then used as a Replica Exchange schedule.
In case the sequence of tempering parameters is longer than the user-defined maximum number of replicas, the schedule is "down-sampled" to the maximum number of replicas (at the cost of lower acceptance rates).


This module thus contains an implementation of WHAM (in `dos_estimators.py`) and a schedule optimizer which consumes the WHAM results to estimate Replica Exchange schedules with the desired target acceptance rate.
