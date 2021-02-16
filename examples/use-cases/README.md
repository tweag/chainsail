# Example RESAAS use cases
This provides several simple use cases for RESAAS, in which a single Markov chain fails to accurately sample a multimodal distribution. 
Each use case consists of several files:
- a `probability.py`, in which the PDF to be sampled as well as an initial state is specified and which can be consumed by the runners via the controller app,
- a script `single_chain.py` which samples from the PDF using a single Markov chain constructed by a very simple Metropolis algorithm and shows the result,
- a script `compare.py` which compares the results of single-chain sampling and results obtain by Replica Exchange via RESAAS,
- and potentially a script `make_data.py`, which creates a data set, from which parameters of a Bayesian model are inferred.

The typical workflow to try out these use cases would be
1. run `python single_chain.py` in one of the use case directories and be unhappy with the result,
2. run RESAAS using the same `probability.py`; for these simple use cases preferably locally according to [these instructions](../../app/controller/),
3. load the RESAAS results and store them in a single `numpy` array written to the use case directory by running (in this directory)
```bash
$ poetry shell
$ python resaas_results_local.py <local controller basename argument> production_run <use case directory>
```
, where the first argument is what you gave as the `--basename` argument to the local controller run script, the second argument denotes either an optimization run (`optimization_run0` (1, 2, ...), mostly for debug purposes) or, ususally, the `production_run`and the third argument is the use case directory (`mixture`, `or-line-fitting`),
4. run `python compare.py 0` in the use case directory and be amazed how much better RESAAS sampled your distribution. The only argument to `compare.py` is the replica index; `0` corresponds to the target distribution, while higher integers correspond to the increasingly flatter versions. This is nice to illustrate the enhanced sampling in the "flatter" replicas.
