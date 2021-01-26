from abc import abstractmethod, ABC

import yaml
import numpy as np

from resaas.schedule_estimation.dos_estimators import WHAM, BoltzmannEnsemble
from resaas.schedule_estimation.schedule_optimizers import SingleParameterScheduleOptimizer
from resaas.common.storage import SimulationStorage
# from resaas.re_runners import LocalRERunner


def log(msg):
    # TODO
    pass


cfg_template = {
    're': {
        'swap_interval': 5,
        'status_interval': 100,
        'dump_interval': 1000,
        'statistics_update_interval': 100,
        'schedule': None
    },
    'general': {
        'n_iterations': None,
        'basename': None,
        'output_path': None,
        'initial_states': None,
        'num_replicas': None
    },
    'local_sampling': {
        'n_steps': 20,
        'timesteps': None,
        'timestep_adaption_limit': None,
        'adaption_uprate': 1.05,
        'adaption_downrate': 0.95,
    }
}


def schedule_length(schedule):
    return len(list(schedule.values())[0])


def optimization_converged(schedule, previous_schedule):
    '''
    Check for convergence of schedule optimization.

    We say that the optimization converged if two subsequent schedules
    have the same length. There is an off chance that parameter values
    shift while the length stays the same, but for now that'll do.

    Args:
        schedule(dict): a schedule obtained from an iteration
        previous_schedule(dict): schedule obtained from the iteration after
    '''
    return schedule_length(schedule) == schedule_length(previous_schedule)


def setup_timesteps(current_storage, schedule, previous_storage=None):
    '''
    Sets up time steps, possibly based on a previous simulation.

    Args:
        current_storage(:class:`SimulationStorage`): storage for simulation
          to be set up
        schedule(dict): current parameter schedule
        previous_storage(:class:`SimulationStorage`): storage for previous
          simulation
    '''
    if previous_storage is None:
        timesteps = np.linspace(1e-3, 1e-1, len(schedule))
    else:
        old_timesteps = previous_storage.load_timesteps()
        old_schedule = previous_storage.load_schedule()
        timesteps = interpolate_timesteps(schedule, old_schedule,
                                          old_timesteps)
    current_storage.save_timesteps(timesteps)


def interpolate_timesteps(schedule, old_schedule, old_timesteps):
    '''
    Interpolates time steps from a previous simulation.

    Given time steps from a previous simulation and its schedule,
    this interpolates between these time steps to a new schedule
    length.

    Args:
        schedule(dict): current parameter schedule
        old_schedule(dict): previous parameter schedule
        old_timesteps(dict): previous set of time steps
    '''
    # TODO: somehow interpolate timesteps from old simulation, e.g., by
    # fitting spline or just simple linear interpolation
    return np.array([0.001] * schedule_length(schedule))


def draw_initial_states(schedule, previous_storage, dos):
    '''
    Draw initial states using the density of states.

    Given previous samples, their energies, and the current parameter
    schedule, this uses the density of states to calculate probability
    weights of the previous samples under the new schedule and uses
    those weights to sample fitting new initial states from the existing
    samples.

    Args:
        schedule(dict): current temperature schedule
        dos(:class:`np.array`): density of states estimate of previous
          simulation
    '''
    # TODO
    return np.array([0.001] * schedule_length(schedule))


def setup_initial_states(current_storage, schedule, previous_storage=None):
    '''
    Sets up initial states.

    Uses the density of states to draw new initial states and writes them
    to the simulation directory.

    Args:
        current_storage(:class:`SimulationStorage`): storage for simulation
          to be set up
        schedule(dict): current paramter schedule
        previous_storage(:class:`SimulationStorage`): storage for previous
          simulation
    '''
    if previous_storage is not None:
        dos = previous_storage.load_dos()
        initial_states = draw_initial_states(
            schedule, previous_storage, dos)
        current_storage.save_initial_states(initial_states)


class AbstractInitialScheduleMaker(ABC):
    '''
    Interface for classes which are responsible for creating
    initial schedules.
    '''

    def __init__(self, param_name):
        self._param_name = param_name

    @abstractmethod
    def make_initial_schedule(self, **params):
        '''
        Make an initial schedule from some parameters.
        '''
        pass


class GeometricInitialScheduleMaker(AbstractInitialScheduleMaker):
    '''
    Schedule maker which makes a schedule using a geometric progression.
    '''

    def make_initial_schedule(self, num_replicas, min_value, max_value=1.0):
        '''
        Makes a schedule of replica parameters (usually inverse temperatures)
        with a fixed length defined by a geometric progression.

        Args:
            num_replicas(int): number of replicas
            min_value(float): minimum parameter value
            max_value(float): maximum parameter value
        '''
        common_ratio = (max_value / min_value) ** (1. / num_replicas)
        geometric_progression = common_ratio ** np.arange(num_replicas)
        return {self._param_name: geometric_progression}


class AbstractREJobController(ABC):
    '''
    Interface for Replica Exchange job controllers. They implement the main
    loop of running a simulation, optimizing the schedule, determining new
    initial states for the next simulation, setting it up and running it.
    '''

    def __init__(self, job_spec, re_runner, storage, schedule_optimizer,
                 dos_estimator,
                 initial_schedule_maker=GeometricInitialScheduleMaker,
                 base_name=''):
        '''
        Initializes a Replica Exchange job controller.

        Arguments contain everything required for running simulations and
        optimizing schedules.

        Args:
            job_spec(dict): job specifications provided by the user
            re_runner(:class:`AbstractRERunner`): runner which runs an RE
              simulation (depends on the environment) 
            base_storage(:class:`AbstractStorage`:): storage backend for
              reading / writing strings from / to permanent simulation storage
            schedule_optimizer(:class:`AbstractScheduleOptimizer`): schedule
              optimizer which calculates a new schedule based on
              an estimate for the density of states
            dos_estimator(:class:`WHAM`): WHAM object which estimates the
              density of states from samples of a previous simulation
            initial_schedule_maker(:class:`InitialScheduleMaker`): schedule
              maker object which calculates a very first Replica Exchange
              schedule
            base_name(str): optional basename to the simulation storage path
              (required for running locally or when reusing an existing bucket)
        '''
        self._re_runner = re_runner
        self._initial_schedule_maker = initial_schedule_maker
        self._schedule_optimizer = schedule_optimizer
        self._dos_estimator = dos_estimator
        self._storage_backend = storage_backend
        self._base_name = base_name
        self._re_params = job_spec['re_params']
        self._local_sampling_params = job_spec['local_sampling_params']
        self._optimization_params = job_spec['optimization_params']
        self._initial_schedule_params = job_spec['initial_schedule_params']

    @abstractmethod
    def _scale_environment(self, num_replicas):
        '''
        Scale up / down the environment to the given numer of replicas.

        Args:
            num_replicas(int): number of replicas
        '''
        pass

    def _calculate_schedule_from_dos(self, previous_storage, dos):
        '''
        Calculates an optimized schedule given a previous simulation and its
        resulting density of states estimate.

        Args:
            dos(:class:`np.array`): the density of states estimate obtained from
              the previous simulation

        Returns:
            dict: optimized schedule
        '''
        energies = self._storage.load_energies()
        schedule = self._schedule_optimizer.optimize(dos, energies)

        return schedule

    def optimize_schedule(self):
        '''
        Run schedule optimization loop.

        This is the main loop in this class: first, an initial schedule is
        calculated and a very first simulation is run. Its samples are then
        used to calculate an estimate of the density of states, which is then
        used to calculate the schedule and initial states for the next
        optimization run..
        Its results are then used to improve the schedule in another run and
        so on and so forth.
        '''
        dos = None
        previous_schedule = None
        previous_storage = None
        opt_params = self._optimization_params

        max_runs = opt_params['max_optimization_runs']
        for run_counter in range(max_runs):
            log('Schedule optimization simulation #{}/{} started'.format(
                run_counter + 1, max_runs))
                current_storage = SimulationStorage(
                    self._basename, 'optimization_run{}'.format(run_counter),
                    self._storage_backend)
            if previous_schedule is not None:
                schedule = self._calculate_schedule_from_dos(
                    previous_storage, dos)
                msg_part1 = 'Calculated schedule for optimization run '
                msg_part2 = '{}/{} with {} replicas'.format(
                    run_counter, max_runs, schedule_length(schedule))
                log(msg_part1 + msg_part2)
            else:
                schedule = self._initial_schedule_maker.make_initial_schedule()

            self._setup_simulation(current_storage, schedule, previous_storage)
            self._do_single_run(storage)
            dos = self._storage.load_dos()

            if previous_schedule is not None and optimization_converged(
                schedule, previous_schedule):
                break

            previous_storage = storage
            previous_schedule = schedule
        else:
            log(('Maximum number of optimization runs reached. '
                 'Schedule optimization might not have converged'))
        final_schedule = self._calculate_schedule_from_dos(
            current_storage, dos)

        return storage, final_schedule

    def _fill_config_template(self, storage, previous_storage, schedule,
                              prod=False):
        '''
        Fills in the config template with run-specific values.

        Args:
            current_storage(:class:`SimulationStorage`): storage for simulation
              to be set up
            previous_storage(:class:`SimulationStorage`): storage for previous
              simulation
            schedule(dict): schedule of the current simulation
            prod(bool): whether this is the production run or not
        '''
        updates = {'local_sampling': {}, 'general': {}, }
        adapt_limit = self._local_sampling_params['hmc_num_adaption_steps']
        updates['local_sampling']['timestep_adaption_limit'] = adapt_limit
        if previous_storage is not None:
            updates['local_sampling'] = {
                'timesteps': dir_structure.TIMESTEPS_FILE_NAME}
            updates['general'] = {
                'initial_states': dir_structure.INITIAL_STATES_PATH}
        if prod:
            num_samples = self._re_params['num_production_samples']
        else:
            num_samples = self._re_params['num_optimization_samples']
        updates['general'] = {'n_iterations': num_samples,
                              'output_path': storage.sim_path,
                              'num_replicas': schedule_length(schedule),
                              'basename': storage._basename}
        updates['re'] = {'schedule': dir_structure.SCHEDULE_PATH,
                         'dump_interval': self._re_params['dump_interval']}

        return updates

    def _setup_simulation(self, schedule, previous_storage=None,
                          prod=False):
        '''
        Sets up a simulation such that a RE runner only has to start it.

        Setting up a simulation involves determining initial values for local
        sampling, writing them to the simulation folder, completing the
        simulation config and using it to write a config file to the simulation
        folder.

        Args:
            schedule(dict): Replica Exchange schedule
            previous_storage(:class:`SimulationStorage`): storage for previous
              simulation
            prod(bool): whether this is the production run or not
        '''
        if previous_storage is not None:
            self._initial_value_setuper.setup_timesteps(storage, schedule,
                                                        previous_storage)
            self._initial_value_setuper.setup_initial_states(
                storage, schedule, previous_storage)

        config_dict = self._fill_config_template(storage, previous_storage,
                                                 schedule, prod)
        config = yaml.dump(config_dict)
        self._storage.save_config(config)
        self._storage.save_schedule(schedule)
        self._scale_environment(schedule_length(schedule))

    def _do_single_run(self, storage):
        '''
        Run a single Replica Exchange simulation, estimate the density of
        states and write it to the simulation folder.

        Args:
            current_storage(:class:`SimulationStorage`): storage for simulation
              to be set up

        Returns:
          :class:`np.array`: density of states estimate
        '''
        self._re_runner.run_sampling(storage.config_file_name)
        energies = self._storage.load_all_energies()
        schedule = self._storage.load_schedule()
        dos = self._dos_estimator.estimate_dos(energies, schedule)
        self._storage.save_dos(dos)

    def _check_compatibility(self, initial_schedule_params,
                             optimization_params):
        '''
        Check whether initial schedule parameters are compatible with the
        optimization parameters.

        Args:
            initial_schedule_params(dict): initial schedule parameters
            optimization_params(dict): optimization params
        '''
        # TODO: check whether optimization params and initial schedule params
        # are compatible. Although that's a late failure - perhaps do this upon
        # job submission?
        pass

    def run_job(self):
        '''
        Runs a complete Replica Exchange sampling job.

        This comprises schedule optimization and a final production run.
        '''
        self._check_compatibility(self._initial_schedule_params,
                                  self._optimization_params)

        optimization_result = self._optimize_schedule()
        final_opt_storage, final_schedule = optimization_result

        prod_storage = SimulationStorage(self._basename, 'production_run')
        self._setup_simulation(prod_storage, final_schedule,
                               final_opt_storage, prod=True)
        self._do_single_run(prod_storage.config_file_name)


class LocalREJobController(AbstractREJobController):
    '''
    Local Replica Exchange job controller, which does not scale up / down
    the environment.
    '''

    def _scale_environment(self, _):
        pass


# job_spec = dict(re_params=dict(num_replicas=8, num_optimization_samples=5000),
#                 local_sampling_params=dict(hmc_num_adaption_steps=100),
#                 optimization_params=dict(target_value=0.3, max_param=1,
#                                          min_param=0.1, decrement=0.05),
#                 initial_schedule_params=dict(beta_min=0.01, beta_ratio=0.9),
#                 path='/tmp/jctest/')

# c = LocalREJobController(job_spec, MockRERunner())
# c.run_job()
