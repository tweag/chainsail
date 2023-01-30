Miscellaneous code shared by multiple Chainsail applications.
New users / developers might most likely be interested in
- the [job specification](./chainsail/common/spec.py), which is the reference for all user-tunable knobs in Chainsail that don't require code changes. Note that a good deal of the parameters are not documented.
- the supported local MCMC samplers in [`./chainsail/common/samplers/`](./chainsail/common/samplers/),
- the supported tempering schemes in [`./chainsail/common/tempering/tempered_distributions.py`](/chainsail/common/tempered_distributions.py).

Other code in there includes the storage interface and -backends, configuration schemas for several Chainsail applications, the (very minimal) interface for runners, and loggers.
