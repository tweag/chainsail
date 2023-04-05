# Controller

The job controller application runs single sampling jobs as submitted by the client to the scheduler. Invoking the controller
will execute the sampling job, exposing a gRPC endpoint for health monitoring.
Running a single sampling job entails optimizing the schedule parameters and performing a production run.
Optimizing the schedule is an iterative procedure consisting of the following steps:
1. perform a Replica Exchange run using a [runner](/lib/runners/)
2. estimate the density of states (DOS) from the results using multiple histogram reweighting ([implementation](../../lib/schedule_estimation/chainsail/schedule_estimation/dos_estimators.py))
3. determine improved schedule with approximatively constant acceptance rates based on DOS estimate ([implementation](../../lib/schedule_estimation/chainsail/schedule_estimation/schedule_optimizers.py))
4. draw initial states for the next iteration's simulation by reweighting samples using the DOS estimate ([implementation](./chainsail/controller/initial_setup.py)) and interpolate sampling stepsizes

For the very first run, an initial schedule is determined heuristically. Currently, the only option is a schedule that follows a geometric progression in an inverse temperature-like parameter.
These for points are iterated several times, until finally a production run is started with an optimized schedule and good initial states.

## Replica Exchange sampling runners

This application can use any implementation of [AbstractRERunner](/lib/runners/).
The runner class is specified in the controller configuration file and is loaded *at runtime*.
The controller comes packaged with builtin runners as package extras and they must be installed explicitly.

Available runners:

* `rexfw` -> `poetry install --extras rexfw`

## Configuration

When the full stack (scheduler + client) is deployed, the controller is set up using a config file.
See the example in [../scheduler/example/controller.yaml](../scheduler/example/controller.yaml).

## Running the controller as a stand-alone local app
The controller can be used as a stand-alone app on a single machine. To that end,
1. Make sure you have any system dependencies for the runner installed (`rexfw` requires `openmpi`, for example, provided in the [Nix shell](../../shell.nix)).
2. Make sure that your `probability.py` file that defines the log-probability you want to sample is in this directory. Examples for valid probability definitions can be found [here](https://github.com/tweag/chainsail-resources/tree/main/examples).
3. Install the controller app with the necessary runner (currently, there's only the `rexfw` runner) via `poetry install --extras rexfw`,
4. Install the Python dependencies of your `probability.py` in the Poetry virtual environment via
   ```bash
   $ poetry shell
   $ pip install numpy scipy anotherpackage
   ```
5. Prepare a job configuration JSON file (an example is provided [here](https://github.com/tweag/chainsail-resources/tree/main/examples/job.json)).
6. execute the local controller run script via
   ```bash
   $ poetry run chainsail-controller-local --job-spec <job config file> --dirname <some file system path>
   ```

, which will run the main optimization loop and a production run and write all results to the directory specified via the `--dirname` argument.


## Development workflow

This is the development workflow for working with the controller locally.

1. Enter the dev shell:

```bash
nix develop .#controller
```

2. Edit `../../lib/runners/rexfw/pyproject.toml` to add dependencies necessary to run the `probability.py`. e.g.

```toml
chainsail-helpers = "*"
scipy = "*"
pymc = "*"
```

3. Update the `poetry.lock` for the controller to bring in the additional dependencies:

```sh-session
$ poetry lock --no-update
```

4. Exit and re-enter the controller dev shell

```bash
exit
nix develop .#controller
```

5. You will find that you have a Python interpreter on your PATH with the necessary dependencies:

```sh-session
$ which python
/nix/store/4834b5pqk6fsn1sjh1mrpwdln9jw5nrj-python3-3.10.9-env/bin/python
```

6. Then, assuming you have [chainsail-resources](https://github.com/tweag/chainsail-resources/) cloned at the same level as [chainsail](https://github.com/tweag/chainsail) and you have a job.json in the `./app/controller` directory such as  [job.json](https://gist.github.com/steshaw/10edb377b89a5c315d92c3c2e40454ea), you can run the following examples from `chainsail-resources`.

```bash
PYTHONPATH=../../../chainsail-resources/examples/mixture/ chainsail-controller-local --job-spec=job.json --dirname=/tmp/out
```

```bash
PYTHONPATH=../../../chainsail-resources/examples/pymc-mixture/ chainsail-controller-local --job-spec=job.json --dirname=/tmp/out
```

```bash
$ PYTHONPATH=../../../chainsail-resources/examples/soft-kmeans/ chainsail-controller-local --job-spec=job.json --dirname=/tmp/out
```

7. You can edit local source files and they will be reflected the next time you run `chainsail-controller-local`.

### Direnv

There is `direnv` support supplied by [`../../.envrc`](../../.envrc). So, instead of `nix develop .#controller`, you can also enter a controller dev shell using `direnv allow`.

If you like to use VS Code, you can install [direnv-vscode](https://marketplace.visualstudio.com/items?itemName=mkhl.direnv) to enable Python tooling. VSCode uses Pylance from Microsoft, powered by Pyright.
