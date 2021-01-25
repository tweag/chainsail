from abc import abstractmethod, ABC

import yaml
import numpy as np

from resaas.schedule_estimation.dos_estimators import WHAM, BoltzmannEnsemble
from resaas.schedule_estimation.schedule_optimizers import SingleParameterScheduleOptimizer
from resaas.schedule_estimation.optimization_quantities import acceptance_rate
# from resaas.re_runners import LocalRERunner


def log(msg):
    # TODO
    pass


TIMESTEPS_PATH = 'timesteps.pickle'
FINAL_TIMESTEPS_PATH = 'final_timesteps.pickle'
INITIAL_STATES_PATH = 'initial_states.pickle'
DOS_PATH = 'dos.pickle'
FINAL_DOS_PATH = 'final_dos.pickle'
SCHEDULE_PATH = 'schedule.pickle'
PROD_OUTPUT_PATH = 'production_run/'
ENERGIES_PATH = 'energies/'
CONFIG_PATH = 'config.yml'


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


def load_energies(sim_path, pickle_storage, string_storage):
    '''
    Loads energies from a simulation.

    Args:
      sim_path(str): path of the simulation
      pickle_storage(:class:`AbstractStorage): storage backend for pickleing /
          unpickleing Python objects to / from permanent storage
      string_storage(:class:`AbstractStorage`:): storage backend for reading /
          writing strings from / to permanent storage
    '''
    # TODO: I didn't manage to mock this function using unittest.mock,
    # so this has to be commented out for the test :-(
    # return np.eye(len(pickle_storage.read(sim_path + 'schedule.pickle')['beta']))
    config = yaml.safe_load(string_storage.read(sim_path + CONFIG_PATH))
    n_replicas = config['general']['num_replicas']
    n_samples = config['general']['n_iterations']
    dump_interval = config['re']['dump_interval']
    energies = []
    for r in range(1, n_replicas + 1):
        r_energies = []
        for n in range(0, n_samples - dump_interval, dump_interval):
            fname = 'energies_replica{}_{}-{}.pickle'.format(
                r, n, n + dump_interval)
            r_energies.append(pickle_storage.read(
                sim_path + ENERGIES_PATH + fname))
        energies.append(np.concatenate(r_energies))
    return np.array(energies)


class InitialValueSetuper:
    '''
    Sets up an initial values for local sampling.
    '''

    def __init__(self, pickle_storage):
        '''
        Initialize a schedule setuper.

        Args:
          pickle_storage(:class:`AbstractStorage`): storage backend for pickled
                                                    Python objects
        '''
        self._pickle_storage = pickle_storage

    def setup_timesteps(self, sim_path, schedule, previous_sim_path=None):
        '''
        Sets up time steps, possibly based on a previous simulation.

        Args:
          sim_path(str): path of current simulation
          schedule(dict): current parameter schedule
          previous_sim_path(str): path of previous simulation
        '''
        if previous_sim_path is None:
            timesteps = np.linspace(1e-3, 1e-1, len(schedule))
        else:
            old_timesteps = self._pickle_storage.read(
                previous_sim_path + FINAL_TIMESTEPS_PATH)
            old_schedule = self._pickle_storage.read(
                previous_sim_path + SCHEDULE_PATH)
            timesteps = self._interpolate_timesteps(schedule, old_schedule,
                                                    old_timesteps)
        self._pickle_storage.write(timesteps,
                                   sim_path + TIMESTEPS_PATH)

    def _interpolate_timesteps(self, schedule, old_schedule, old_timesteps):
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

    def _draw_initial_states(self, schedule, previous_sim_path, dos):
        '''
        Draw initial states using the density of states.

        Given previous samples, their energies, and the current parameter
        schedule, this uses the density of states to calculate probability
        weights of the previous samples under the new schedule and uses
        those weights to sample fitting new initial states from the existing
        samples.

        Args:
          schedule(dict): current temperature schedule
          previous_sim_path(dict): path of previous simulation
          dos(:class:`np.array`): density of states estimate of previous
              simulation
        '''
        # TODO
        return np.array([0.001] * schedule_length(schedule))

    def setup_initial_states(self, sim_path, schedule,
                             previous_sim_path=None):
        '''
        Sets up initial states.

        Uses the density of states to draw new initial states and writes them
        to the simulation directory.

        Args:
          sim_path(str): path of current simulation
          schedule(dict): current paramter schedule
          previous_sim_path(str): path of previous simulation
        '''
        if previous_sim_path is not None:
            dos = self._pickle_storage.read(previous_sim_path + DOS_PATH)
            initial_states = self._draw_initial_states(schedule,
                                                       previous_sim_path,
                                                       dos)
            self._pickle_storage.write(initial_states,
                                       sim_path + INITIAL_STATES_PATH)


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

    def __init__(self, job_spec, re_runner, pickle_storage, string_storage,
                 initial_schedule_maker=GeometricInitialScheduleMaker,
                 schedule_optimizer=SingleParameterScheduleOptimizer,
                 ensemble=BoltzmannEnsemble,
                 optimization_quantity=acceptance_rate,
                 dos_estimator=WHAM):
        '''
        Initializes a Replica Exchange job controller.

        Arguments contain everything required for running simulations and
        optimizing schedules.

        Args:
          job_spec(dict): job specifications provided by the user
          re_runner(:class:`AbstractRERunner`): runner which runs an RE
              simulation (depends on the environment) 
          pickle_storage(:class:`AbstractStorage): storage backend for
              pickleing / unpickleing Python objects to / from permanent
              storage
          string_storage(:class:`AbstractStorage`:): storage backend for
              reading / writing strings from / to permanent storage
          initial_schedule_maker(:class:`InitialScheduleMaker`): schedule
              maker objects which calculates a very first Replica Exchange
              schedule
          schedule_optimizer(:class:`AbstractScheduleOptimizer`): schedule
              optimizer class which calculates a new schedule based on
              an estimate for the density of states
          ensemble(:class:`AbstractEnsemble`): the ensemble (family of
              tempered distributions) to use
          optimization_quantity(callable): the quantitiy which controls
              schedule optimization
          dos_estimator(:class:`WHAM`): WHAM implementation which estimates the
              density of states from samples of a previous simulation
        '''
        self._re_runner = re_runner
        self._initial_schedule_maker = initial_schedule_maker
        self._schedule_optimizer = schedule_optimizer
        self._ensemble = ensemble
        self._optimization_quantity = optimization_quantity
        self._dos_estimator = dos_estimator
        self._basename = job_spec['path']
        self._pickle_storage = pickle_storage
        self._string_storage = string_storage
        self._initial_value_setuper = InitialValueSetuper(
            self._pickle_storage)
        self._re_params = None
        self._local_sampling_params = None
        self._optimization_params = None
        self._set_params(job_spec)

    def _set_params(self, job_spec):
        '''
        Set different parameter dictionaries from job specification.

        Args:
          job_spec(dict): job specification
        '''
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

    def _calculate_schedule_from_dos(self, previous_sim_path, dos):
        '''
        Calculates an optimized schedule given a previous simulation and its
        resulting density of states estimate.

        Args:
          previous_sim_path(str): path of previous simulation
          dos(:class:`np.array`): the density of states estimate obtained from
              the previous simulation

        Returns:
          dict: optimized schedule
        '''
        energies = load_energies(previous_sim_path, self._pickle_storage,
                                 self._string_storage)
        # TODO: refactoring required; have user instantiate schedule optimizer
        optimizer = self._schedule_optimizer(dos, energies,
                                             acceptance_rate, 'beta')
        params_copy = dict(self._optimization_params)
        params_copy.pop('max_optimization_runs')
        schedule = optimizer.optimize(**params_copy)

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
        previous_sim_path = None
        opt_params = self._optimization_params

        max_runs = opt_params['max_optimization_runs']
        for run_counter in range(max_runs):
            log('Schedule optimization simulation #{}/{} started'.format(
                run_counter + 1, max_runs))
            sim_path = 'optimization_run{}/'.format(run_counter)
            if previous_schedule is not None:
                schedule = self._calculate_schedule_from_dos(
                    previous_sim_path, dos)
                msg_part1 = 'Calculated schedule for optimization run '
                msg_part2 = '{}/{} with {} replicas'.format(
                    run_counter, max_runs, schedule_length(schedule))
                log(msg_part1 + msg_part2)
            else:
                sched_maker = self._initial_schedule_maker()
                schedule = sched_maker.make_initial_schedule(
                    **self._initial_schedule_params)

            self._setup_simulation(sim_path, schedule, previous_sim_path)
            self._do_single_run(sim_path)
            dos = self._pickle_storage.read(sim_path + DOS_PATH)

            if previous_schedule is not None and optimization_converged(
                schedule, previous_schedule):
                break

            previous_sim_path = sim_path
            previous_schedule = schedule
        else:
            log(('Maximum number of optimization runs reached. '
                 'Schedule optimization might not have converged'))
        final_schedule = self._calculate_schedule_from_dos(sim_path, dos)

        return sim_path, final_schedule, dos

    def _fill_config_template(self, sim_path, previous_sim_path, schedule,
                              prod=False):
        '''
        Fills in the config template with run-specific values.

        Args:
          sim_path(str): path of the current simulation
          previous_sim_path(str): path of the previous simulation
          schedule(dict): schedule of the current simulation
          prod(bool): whether this is the production run or not
        '''
        updates = {'local_sampling': {}, 'general': {}, }
        adapt_limit = self._local_sampling_params['hmc_num_adaption_steps']
        updates['local_sampling']['timestep_adaption_limit'] = adapt_limit
        if previous_sim_path is not None:
            updates['local_sampling'] = {
                'timesteps': sim_path + TIMESTEPS_PATH}
            updates['general'] = {
                'initial_states': sim_path + INITIAL_STATES_PATH}
        if prod:
            num_samples = self._re_params['num_production_samples']
        else:
            num_samples = self._re_params['num_optimization_samples']
        updates['general'] = {'n_iterations': num_samples,
                              'output_path': sim_path,
                              'num_replicas': schedule_length(schedule),
                              'basename': self._basename}
        updates['re'] = {'schedule': sim_path + SCHEDULE_PATH,
                         'dump_interval': self._re_params['dump_interval']}

        return updates

    def _setup_simulation(self, sim_path, schedule, previous_sim_path=None,
                          prod=False):
        '''
        Sets up a simulation such that a RE runner only has to start it.

        Setting up a simulation involves determining initial values for local
        sampling, writing them to the simulation folder, completing the
        simulation config and using it to write a config file to the simulation
        folder.

        Args:
          sim_path(str): path of the simulation
          schedule(dict): Replica Exchange schedule
          previous_sim_path(str): path of previous simulation
          prod(bool): whether this is the production run or not
        '''
        if previous_sim_path is not None:
            self._initial_value_setuper.setup_timesteps(sim_path, schedule,
                                                        previous_sim_path)
            self._initial_value_setuper.setup_initial_states(
                sim_path, schedule, previous_sim_path)

        config_dict = self._fill_config_template(sim_path, previous_sim_path,
                                                 schedule, prod)
        config = yaml.dump(config_dict)
        self._string_storage.write(config, sim_path + CONFIG_PATH,
                                   mode_flags='w')
        self._pickle_storage.write(schedule, sim_path + SCHEDULE_PATH)
        self._scale_environment(schedule_length(schedule))

    def _do_single_run(self, sim_path):
        '''
        Run a single Replica Exchange simulation, estimate the density of
        states and write it to the simulation folder.

        Args:
          sim_path(str): path of the simulation

        Returns:
          :class:`np.array`: density of states estimate
        '''
        self._re_runner.run_sampling(sim_path + CONFIG_PATH, self._basename)
        energies = load_energies(sim_path, self._pickle_storage,
                                 self._string_storage)
        schedule = self._pickle_storage.read(sim_path + SCHEDULE_PATH)
        dos_estimator = self._dos_estimator(energies, self._ensemble, schedule)
        dos = dos_estimator.estimate_dos()
        self._pickle_storage.write(dos, sim_path + DOS_PATH)

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
        final_opt_sim_path, final_schedule = optimization_result

        self._setup_simulation(PROD_OUTPUT_PATH, final_schedule,
                               final_opt_sim_path, prod=True)
        self._do_single_run(PROD_OUTPUT_PATH)


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
