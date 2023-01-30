Local MCMC samplers supported by Chainsail.
These are currently very simple and should soon be extended with state-of-the-art methods such as NUTS.
Currently implemented are:
- a Metropolis sampler with a uniform proposal distribution (`rwmc.py`),
- a Hybrid / Hamiltonian Monte Carlo (HMC) sampler (`hmc.py`).

Both have a very simple heuristic stepsize adaption scheme that :warning: breaks detailed balance :warning:.
