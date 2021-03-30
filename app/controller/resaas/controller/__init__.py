import logging
import time
from dataclasses import asdict

import requests
from resaas.common.spec import (
    BoltzmannInitialScheduleParameters,
    TemperedDistributionFamily,
    get_sampler_from_params,
)
from resaas.common.storage import SimulationStorage
from resaas.common.storage import default_dir_structure as dir_structure
from resaas.common.tempering.ensembles import BoltzmannEnsemble
from resaas.controller.initial_schedules import make_geometric_schedule
from resaas.controller.initial_setup import setup_initial_states, setup_stepsizes
from resaas.controller.util import schedule_length
from resaas.schedule_estimation.dos_estimators import WHAM
from resaas.schedule_estimation.optimization_quantities import get_quantity_function
from resaas.schedule_estimation.schedule_optimizers import SingleParameterScheduleOptimizer

logger = logging.getLogger(__name__)


def _config_template_from_params(re_params, local_sampling_params):
    """
    Makes a nested dictionary from parameter dataclasses.

    This dictionary is then completed with run-specific values and serialized
    to a YAML file.
    """
    re = asdict(re_params)
    re["schedule"] = None
    re.pop("num_optimization_samples")
    re.pop("num_production_samples")
    local_sampling = asdict(local_sampling_params)
    local_sampling["stepsizes"] = None
    local_sampling["sampler"] = get_sampler_from_params(local_sampling_params).value
    general = dict(
        n_iterations=None, basename=None, output_path=None, initial_states=None, num_replicas=None
    )

    return dict(re=re, local_sampling=local_sampling, general=general)


def params_from_job_spec(job_spec):
    re_params = job_spec.replica_exchange_parameters
    ls_params = job_spec.local_sampling_parameters
    opt_params = job_spec.optimization_parameters

    return re_params, ls_params, opt_params


def optimization_converged(schedule, previous_schedule):
    """
    Check for convergence of schedule optimization.

    We say that the optimization converged if two subsequent schedules
    have the same length. There is an off chance that parameter values
    shift while the length stays the same, but for now that'll do.

    Args:
        schedule(dict): a schedule obtained from an iteration
        previous_schedule(dict): schedule obtained from the iteration after
    """
    return schedule_length(schedule) == schedule_length(previous_schedule)


def optimization_objects_from_spec(job_spec):
    """
    Instantiates DOS estimator, schedule optimizer and initial
    schedule from a job specification.

    Args:
        job_spec(:class:`JobSpec`): job specification
    """
    dist_family = job_spec.tempered_dist_family
    sched_parameters = job_spec.initial_schedule_parameters
    init_num_replicas = job_spec.initial_number_of_replicas

    if dist_family == TemperedDistributionFamily.BOLTZMANN:
        if type(sched_parameters) == BoltzmannInitialScheduleParameters:
            opt_params = job_spec.optimization_parameters
            dos_estimator = WHAM(BoltzmannEnsemble)
            schedule_optimizer = SingleParameterScheduleOptimizer(
                opt_params.optimization_quantity_target,
                1.0,
                sched_parameters.minimum_beta,
                opt_params.decrement,
                get_quantity_function(opt_params.optimization_quantity),
                "beta",
                job_spec.max_replicas,
            )

            initial_schedule = make_geometric_schedule(
                "beta", init_num_replicas, sched_parameters.minimum_beta, 1.0
            )
        else:
            raise ValueError(
                (
                    f"Initial schedule parameters '{sched_parameters}' not copmatible "
                    f"with tempered distribution family '{dist_family}'."
                )
            )

        return dict(
            dos_estimator=dos_estimator,
            schedule_optimizer=schedule_optimizer,
            initial_schedule=initial_schedule,
        )
    else:
        raise ValueError(f"Invalid distribution family '{dist_family}'")


class BaseREJobController:
    """
    Interface for Replica Exchange job controllers. They implement the main
    loop of running a simulation, optimizing the schedule, determining new
    initial states for the next simulation, setting it up and running it.
    """

    def __init__(
        self,
        re_params,
        local_sampling_params,
        optimization_params,
        re_runner,
        storage_backend,
        schedule_optimizer,
        dos_estimator,
        initial_schedule,
        basename="",
    ):
        """
        Initializes a basic Replica Exchange job controller, which can be used
        locally independently from the scheduler and other RESAAS components.

        Arguments contain everything required for running simulations and
        optimizing schedules.

        Args:
            re_params(:class:`ReplicaExchangeParameters`): Replica Exchange-
              specific parameters
            local_sampling_params(:class:`NaiveHMCParameters`): local sampling-
              specific parameters
            optimization_params(:class:`OptimizationParameters`): schedule
              optimization-related parameters
            re_runner(:class:`AbstractRERunner`): runner which runs an RE
              simulation (depends on the environment)
            base_storage(:class:`AbstractStorage`:): storage backend for
              reading / writing strings from / to permanent simulation storage
            schedule_optimizer(:class:`AbstractScheduleOptimizer`): schedule
              optimizer which calculates a new schedule based on
              an estimate for the density of states
            dos_estimator(:class:`WHAM`): WHAM object which estimates the
              density of states from samples of a previous simulation
            initial_schedule(dict`): initial parameter schedule
              maker object which calculates a very first Replica Exchange
              schedule
            basename(str): optional basename to the simulation storage path
              (required for running locally or when reusing an existing bucket)
        """
        self._re_runner = re_runner
        self._initial_schedule = initial_schedule
        self._schedule_optimizer = schedule_optimizer
        self._dos_estimator = dos_estimator
        self._storage_backend = storage_backend
        self._basename = basename
        self._re_params = re_params
        self._local_sampling_params = local_sampling_params
        self._optimization_params = optimization_params

    def _scale_environment(self, num_replicas):
        """
        Scale up / down the environment to the given numer of replicas.

        Args:
            num_replicas(int): number of replicas
        """
        pass

    def _calculate_schedule_from_dos(self, previous_storage, dos):
        """
        Calculates an optimized schedule given a previous simulation and its
        resulting density of states estimate.

        Args:
            previous_storage(:class:`SimulationStorage`): storage for previous
              simulation
            dos(:class:`np.array`): the density of states estimate obtained from
              the previous simulation

        Returns:
            dict: optimized schedule
        """
        energies = previous_storage.load_all_energies(
            *self._get_dos_subsample_params(previous_storage)
        )
        schedule = self._schedule_optimizer.optimize(dos, energies)

        return schedule

    def optimize_schedule(self):
        """
        Run schedule optimization loop.

        This is the main loop in this class: first, an initial schedule is
        calculated and a very first simulation is run. Its samples are then
        used to calculate an estimate of the density of states, which is then
        used to calculate the schedule and initial states for the next
        optimization run..
        Its results are then used to improve the schedule in another run and
        so on and so forth.
        """
        dos = None
        previous_schedule = None
        previous_storage = None
        opt_params = self._optimization_params

        max_runs = opt_params.max_optimization_runs
        for run_counter in range(max_runs):
            logger.info(
                "Schedule optimization simulation #{}/{} started".format(run_counter + 1, max_runs)
            )
            current_storage = SimulationStorage(
                self._basename, "optimization_run{}".format(run_counter), self._storage_backend
            )
            if previous_schedule is not None:
                schedule = self._calculate_schedule_from_dos(previous_storage, dos)
                msg_part1 = "Calculated schedule for optimization run "
                msg_part2 = "{}/{} with {} replicas".format(
                    run_counter, max_runs, schedule_length(schedule)
                )
                logger.info(msg_part1 + msg_part2)
            else:
                schedule = self._initial_schedule

            self._setup_simulation(current_storage, schedule, previous_storage)
            self._do_single_run(current_storage)
            dos = current_storage.load_dos()

            if previous_schedule is not None and optimization_converged(
                schedule, previous_schedule
            ):
                break

            previous_storage = current_storage
            previous_schedule = schedule
        else:
            logger.info(
                (
                    "Maximum number of optimization runs reached. "
                    "Schedule optimization might not have converged"
                )
            )
        final_schedule = self._calculate_schedule_from_dos(current_storage, dos)

        return current_storage, final_schedule

    def _fill_config_template(self, storage, previous_storage, schedule, prod=False):
        """
        Makes a config template template and updates it with run-specific
        values.

        Args:
            current_storage(:class:`SimulationStorage`): storage for simulation
              to be set up
            previous_storage(:class:`SimulationStorage`): storage for previous
              simulation
            schedule(dict): schedule of the current simulation
            prod(bool): whether this is the production run or not
        """
        cfg_template = _config_template_from_params(self._re_params, self._local_sampling_params)
        updates = {
            "local_sampling": {},
            "general": {},
        }
        if previous_storage is not None:
            updates["local_sampling"] = {"stepsizes": dir_structure.INITIAL_STEPSIZES_FILE_NAME}
            updates["general"] = {"initial_states": dir_structure.INITIAL_STATES_FILE_NAME}
        if prod:
            num_samples = self._re_params.num_production_samples
        else:
            num_samples = self._re_params.num_optimization_samples

        num_adaption_samples = cfg_template["local_sampling"]["num_adaption_samples"]
        if num_adaption_samples is None:
            num_adaption_samples = int(0.1 * num_samples)
        updates["local_sampling"]["num_adaption_samples"] = num_adaption_samples

        updates["general"] = {
            "n_iterations": num_samples,
            "output_path": storage.sim_path,
            "num_replicas": schedule_length(schedule),
            "basename": storage._basename,
        }
        updates["re"] = {
            "schedule": dir_structure.SCHEDULE_FILE_NAME,
            "dump_interval": self._re_params.dump_interval,
        }

        for k, v in updates.items():
            cfg_template[k].update(**v)

        return cfg_template

    def _setup_simulation(self, current_storage, schedule, previous_storage=None, prod=False):
        """
        Sets up a simulation such that a RE runner only has to start it.

        Setting up a simulation involves determining initial values for local
        sampling, writing them to the simulation folder, completing the
        simulation config and using it to write a config file to the simulation
        folder.

        Args:
            current_storage(:class:`SimulationStorage`): storage for current
              simulation
            schedule(dict): Replica Exchange schedule
            previous_storage(:class:`SimulationStorage`): storage for previous
              simulation
            prod(bool): whether this is the production run or not
        """
        if previous_storage is not None:
            setup_stepsizes(current_storage, schedule, previous_storage)
            setup_initial_states(
                current_storage,
                schedule,
                previous_storage,
                *self._get_dos_subsample_params(previous_storage),
            )

        config_dict = self._fill_config_template(current_storage, previous_storage, schedule, prod)
        current_storage.save_config(config_dict)
        current_storage.save_schedule(schedule)
        self._scale_environment(schedule_length(schedule))

    def _do_single_run(self, storage):
        """
        Run a single Replica Exchange simulation, estimate the density of
        states and write it to the simulation folder.

        Args:
            storage(:class:`SimulationStorage`): storage for simulation
              to be set up
        """
        self._re_runner.run_sampling(storage)
        energies = storage.load_all_energies(*self._get_dos_subsample_params(storage))
        schedule = storage.load_schedule()
        dos = self._dos_estimator.estimate_dos(energies, schedule)
        storage.save_dos(dos)

    def _get_dos_subsample_params(self, storage):
        num_samples = storage.load_config()["general"]["n_iterations"]
        burnin_percentage = self._optimization_params.dos_burnin_percentage
        thinning_step = self._optimization_params.dos_thinning_step
        from_samples = int(burnin_percentage * num_samples)
        return from_samples, thinning_step

    def run_job(self):
        """
        Runs a complete Replica Exchange sampling job.

        This comprises schedule optimization and a final production run.
        """
        optimization_result = self.optimize_schedule()
        final_opt_storage, final_schedule = optimization_result

        prod_storage = SimulationStorage(self._basename, "production_run", self._storage_backend)
        self._setup_simulation(prod_storage, final_schedule, final_opt_storage, prod=True)
        self._do_single_run(prod_storage)


class CloudREJobController(BaseREJobController):
    SCHEDULER_SCALE_ENDPOINT = "/internal/job/{id}/scale/{n}"
    SCHEDULER_NODE_ENDPOINT = "/job/{id}/nodes"
    SCHEDULER_ADD_ITERATION_ENDPOINT = "/internal/job/{id}/add_iteration/{iteration}"

    def __init__(
        self,
        job_id,
        scheduler_address,
        scheduler_port,
        re_params,
        local_sampling_params,
        optimization_params,
        re_runner,
        storage_backend,
        schedule_optimizer,
        dos_estimator,
        initial_schedule,
        node_updater,
        basename="",
        connection_retries=5,
        connection_retry_interval=1,
        connection_timeout=1200,
        scaling_timeout=1200,
    ):
        """
        Initializes a Replica Exchange job controller which runs within a
        cloud-deployed RESAAS service.

        Arguments contain everything required for running simulations and
        optimizing schedules.

        Args:
            job_id(int): The id of the resaas job to which this controller belongs
            scheduler_address(str): The address to the scheduler
            scheduler_port(int): The scheduler's listening port
            re_params(:class:`ReplicaExchangeParameters`): Replica Exchange-
              specific parameters
            local_sampling_params(:class:`NaiveHMCParameters`): local sampling-
              specific parameters
            optimization_params(:class:`OptimizationParameters`): schedule
              optimization-related parameters
            re_runner(:class:`AbstractRERunner`): runner which runs an RE
              simulation (depends on the environment)
            base_storage(:class:`AbstractStorage`:): storage backend for
              reading / writing strings from / to permanent simulation storage
            schedule_optimizer(:class:`AbstractScheduleOptimizer`): schedule
              optimizer which calculates a new schedule based on
              an estimate for the density of states
            dos_estimator(:class:`WHAM`): WHAM object which estimates the
              density of states from samples of a previous simulation
            initial_schedule(dict`): initial parameter schedule
              maker object which calculates a very first Replica Exchange
              schedule
            node_updater(callable): function which updates information on the
              available nodes after rescaling, e.g., writes a MPI host file. Should only
              accept a single argument, the controller instance.
            basename(str): optional basename to the simulation storage path
              (required for running locally or when reusing an existing bucket)
            connection_retries(int): the number of connection attempts to make when
              contacting the scheduler
            connection_retry_interval(int): the interval in seconds to wait between retries
            connection_timeout(int): connection timeout in seconds
            scaling_timeout(int): timeout for waiting on already running scaling requests
        """
        super().__init__(
            re_params,
            local_sampling_params,
            optimization_params,
            re_runner,
            storage_backend,
            schedule_optimizer,
            dos_estimator,
            initial_schedule,
            basename=basename,
        )
        self.job_id = job_id
        self.scheduler_address = scheduler_address
        self.scheduler_port = scheduler_port
        self._node_updater = node_updater
        self.connection_retries = connection_retries
        self.connection_retry_interval = connection_retry_interval
        self.connection_timeout = connection_timeout
        self.scaling_timeout = scaling_timeout

    def _scale_environment(self, num_replicas):
        """
        Scale up / down the environment to the given numer of replicas.

        Args:
            num_replicas(int): number of replicas
        """
        logger.info(f"Requesting job scaling to {num_replicas}")
        start_time = time.time()
        retries = 0
        while (time.time() - start_time) < self.scaling_timeout:
            try:
                r = requests.post(
                    f"http://{self.scheduler_address}:{self.scheduler_port}{self.SCHEDULER_SCALE_ENDPOINT.format(id=self.job_id, n=num_replicas)}"
                )
                if r.status_code == 409:
                    logger.warn(
                        "Attempted to scale a job which is already scaling. Waiting for "
                        "scaling to finish."
                    )
                    time.sleep(self.connection_retry_interval)
                    continue
                r.raise_for_status()
            except Exception as e:
                retries += 1
                if retries > self.connection_retries:
                    raise e
                time.sleep(self.connection_retry_interval)
                continue
            else:
                break
        self._node_updater(self)

    def _ask_scheduler_to_add_iteration(self, iteration):
        """
        Sends the scheduler a request to add an entry to the list of main controller loop
        iterations.
        """
        for i in range(self.connection_retries):
            try:
                logger.debug(f"Asking scheduler to add controller iteration {iteration}")
                add_iteration_endpoint = self.SCHEDULER_ADD_ITERATION_ENDPOINT.format(
                    id=self.job_id, iteration=iteration
                )
                url = "http://{}:{}{}".format(
                    self.scheduler_address, self.scheduler_port, add_iteration_endpoint
                )
                r = requests.post(url)
                r.raise_for_status()
                break
            except Exception as e:
                logger.error(
                    f"Failed to ask scheduler to add controller iteration {iteration} with response: {repr(r)}"
                )
                if (i + 1) == self.connection_retries:
                    logger.critical(
                        "Used all attempts for asking scheduler to add controller iteration {iteration}."
                    )
                    raise e
                time.sleep(self.connection_retry_interval)

    def _do_single_run(self, storage):
        """
        Run a single Replica Exchange simulation, estimate the density of
        states and write it to the simulation folder.

        Args:
            storage(:class:`SimulationStorage`): storage for simulation
              to be set up
        """
        iteration = storage.sim_path
        self._ask_scheduler_to_add_iteration(iteration)
        super()._do_single_run(storage)


def update_nodes_mpi(
    controller: CloudREJobController,
    hostfile_path,
):
    """
    Writes an updated hostfile which is required by the MPI runner.

    hostfile_path(str): Path at which to read and write the list of host
      addresses which are participating in the job
    """
    # Query the scheduler for a list of peers
    for i in range(controller.connection_retries):
        try:
            logger.debug("Querying peer addresses")
            r = requests.get(
                f"http://{controller.scheduler_address}:{controller.scheduler_port}{controller.SCHEDULER_NODE_ENDPOINT.format(id=controller.job_id)}"
            )
            r.raise_for_status()
        except Exception as e:
            logger.error(
                f"Failed to request peer node list from scheduler with response: {repr(r)}"
            )
            if (i + 1) == controller.connection_retries:
                logger.critical("Used all attempts for requesting node list from scheduler.")
                raise e
            time.sleep(controller.connection_retry_interval)
    hosts = []
    for n in r.json():
        if n["is_worker"] is False:
            logger.debug(f"Ignoring peer node {n['name']} since it is not flagged as worker node.")
            continue
        if n["in_use"]:
            # Note: this may also include t he controller host
            logger.debug(f"Found peer with name: {n['name']}")
            hosts.append(n["address"])
    logger.debug(f"Found a total of {len(hosts)} peers")
    with open(hostfile_path, "w") as f:
        logger.debug(f"Updating hostfile at {hostfile_path}")
        for h in hosts:
            print(h, file=f)
