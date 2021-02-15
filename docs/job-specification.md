# Job specification
To specify a job, the user has to specify:
- `job_name` (string)
- `initial_number_of_replicas` (int)
- `tempered_distribution_family` (string defining the family of tempered distributions to use. For now, the only valid value should be "boltzmann").
- `initial_schedule_parameters` (dictionary with parameters determining the initial tempering schedule from which iterative optimization starts). For now, we support only the [Boltzmann distribution](https://en.wikipedia.org/wiki/Boltzmann_distribution) parameterized by the inverse temperature beta, 0 < beta <= 1. The initial schedule is given by a geometric progression with more tightly spaced temperatures close to beta=1. The initial schedule parameters thus are 
  - `minimum_beta` (float; the minimum inverse temperature (beta) which determines the flatness of the flattest distribution)
  - `initial_schedule_beta_ratio` (float; ratio defining (approximately) the geometric progression) 
- `probability_definition` (URI (s3://... for AWS, gs://... for Google Cloud Storage, ...) to a cloud location including an importable Python module `probability_definition.py` providing an object `pdf` with the interface given in the [`rexfw` example](https://github.com/tweag/rexfw/blob/resaas/rexfw/pdfs/__init__.py). This cloud location also will have to include possible data files and whatever is required to import and evaluate the `Pdf` object.
- `max_nodes` (maximum number of compute nodes to use. Specifics of the environment in which these are created is configured on the scheduler itself)
- `dependencies` (list of dependencies to install on compute nodes, e.g. `[{"type": "pip", "pkgs": ["numpy", "plotly"]}, {type: "nixpkgs", "pkgs": ["opencv", ...]}]` (we can just support pip deps for initial PoC))
The `initial_schedule_parameters` dictionary might allow different entries than the one mentioned above once we support additional families of tempered distributions.
