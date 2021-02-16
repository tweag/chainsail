# Controller

The job controller application runs single sampling jobs as submitted by the client to the scheduler. Invoking the controller
will execute the sampling job, exposing a gRPC endpoint for health monitoring. 
Running a single sampling job entails optimizing the schedule parameters and performing a production run.
Optimizing the schedule is an iterative procedure consisting of the following steps:
1. perform a Replica Exchange run using a [runner](../lib/runners/)
2. estimate the density of states (DOS) from the results using multiple histogram reweighting ([implementation](../../lib/schedule_estimation/resaas/schedule_estimation/dos_estimators.py))
3. determine improved schedule with approximatively constant acceptance rates based on DOS estimate ([implementation](../../lib/schedule_estimation/resaas/schedule_estimation/schedule_optimizers.py))
4. draw initial states for the next iteration's simulation by reweighting samples using the DOS estimate ([implementation](./resaas/controller/initial_setup.py)) and interpolate sampling stepsizes

For the very first run, an initial schedule is determined heuristically. Currently, the only option is a schedule that follows a geometric progression in an inverse temperature-like parameter.

## Replica Exchange sampling runners

This application can use any implementation of [AbstractRERunner](../lib/runners/).
The runner class is specified in the controller configuration file and is loaded *at runtime*.
The controller comes packaged with builtin runners as package extras and they must be installed explicitly. 

Available runners:

* `rexfw` -> `poetry install --extras rexfw`

## Configuration

When the full stack (scheduler + client) is deployed, the controller is set up using a config file.
See the example in [../scheduler/example/controller.yaml](../scheduler/example/controller.yaml).

## Running the controller as a stand-alone local app
The controller can be used as a stand-alone app on a single machine. To that end,
1. make sure you have any eventual system dependencies for the runner installed (`rexfw` requires `openmpi`, for example, provided in the [Nix shell](../../shell.nix))
2. make sure that your `probability.py` file (and everything importet in there) is in this directory,
3. install the controller app with the necessary runner (currently, there's only the `rexfw` runner) via `poetry install --extras rexfw`,
4. install the Python dependencies of your `probability.py` in the Poetry virtual environment via
```bash
$ poetry shell
$ pip install numpy scipy anotherpackage
```
5. prepare a job configuration JSON file (an example is provided in `example_job.json`).
6. execute the local controller run script via
```bash
$ poetry run resaas-controller-local --job_spec <job config file> --basename <some file system path>
```

, which will run the main optimization loop and a production run and write all results to the directory specified via the `--basename` argument.
