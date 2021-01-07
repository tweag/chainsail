# Job specification
To specify a job, the user has to specify:
- `job_name` (string)
- `initial_number_of_replicas` (int)
- `tempered_distribution_family` (string defining the family of tempered distributions to use. For now, the only valid value should be "boltzmann").
- `initial_schedule_parameters` (dictionary with parameters determining the initial tempering schedule from which iterative optimization starts). For now, we support only the [Boltzmann distribution](https://en.wikipedia.org/wiki/Boltzmann_distribution) parameterized by the inverse temperature beta, 0 < beta <= 1. The initial schedule is given by a geometric progression with more tightly spaced temperatures close to beta=1. The initial schedule parameters thus are 
  - `minimum_beta` (float; the minimum inverse temperature (beta) which determines the flatness of the flattest distribution)
  - `initial_schedule_beta_ratio` (float; ratio defining (approximately) the geometric progression) 
- `probability_definition` (URL to archive including importable Python module providing the log probability and, for now, also possible data files)
- `deployment_environment` (string such as "single_vm", "vm_cluster" determining the deployment environment the scheduler works with)

The `initial_schedule_parameters` dictionary might allow different entries than the one mentioned above once we support additional families of tempered distributions.
