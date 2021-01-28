from abc import abstractmethod, ABC

import yaml
import numpy as np

from resaas.schedule_estimation.dos_estimators import WHAM, BoltzmannEnsemble
from resaas.schedule_estimation.schedule_optimizers import SingleParameterScheduleOptimizer
from resaas.common.storage import (
    SimulationStorage, default_dir_structure as dir_structure)
from .initial_setup import setup_initial_states, setup_timesteps
from .util import schedule_length


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


class AbstractREJobController(ABC):
    '''
    Interface for Replica Exchange job controllers. They implement the main
    loop of running a simulation, optimizing the schedule, determining new
    initial states for the next simulation, setting it up and running it.
    '''

    def __init__(self, job_spec, re_runner, storage_backend, schedule_optimizer,
                 dos_estimator, initial_schedule, basename=''):
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
            initial_schedule(dict`): initial parameter schedule
              maker object which calculates a very first Replica Exchange
              schedule
            basename(str): optional basename to the simulation storage path
              (required for running locally or when reusing an existing bucket)
        '''
        self._re_runner = re_runner
        self._initial_schedule = initial_schedule
        self._schedule_optimizer = schedule_optimizer
        self._dos_estimator = dos_estimator
        self._storage_backend = storage_backend
        self._basename = basename
        self._re_params = job_spec['re_params']
        self._local_sampling_params = job_spec['local_sampling_params']
        self._optimization_params = job_spec['optimization_params']

    @classmethod
    def from_job_spec(cls, job_spec):
        

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
            previous_storage(:class:`SimulationStorage`): storage for previous
              simulation
            dos(:class:`np.array`): the density of states estimate obtained from
              the previous simulation

        Returns:
            dict: optimized schedule
        '''
        energies = previous_storage.load_all_energies()
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
                schedule = self._initial_schedule

            self._setup_simulation(current_storage, schedule, previous_storage)
            self._do_single_run(current_storage)
            dos = current_storage.load_dos()

            if previous_schedule is not None and optimization_converged(
                schedule, previous_schedule):
                break

            previous_storage = current_storage
            previous_schedule = schedule
        else:
            log(('Maximum number of optimization runs reached. '
                 'Schedule optimization might not have converged'))
        final_schedule = self._calculate_schedule_from_dos(
            current_storage, dos)

        return current_storage, final_schedule

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
                'timesteps': dir_structure.INITIAL_TIMESTEPS_FILE_NAME}
            updates['general'] = {
                'initial_states': dir_structure.INITIAL_STATES_FILE_NAME}
        if prod:
            num_samples = self._re_params['num_production_samples']
        else:
            num_samples = self._re_params['num_optimization_samples']
        updates['general'] = {'n_iterations': num_samples,
                              'output_path': storage.sim_path,
                              'num_replicas': schedule_length(schedule),
                              'basename': storage._basename}
        updates['re'] = {'schedule': dir_structure.SCHEDULE_FILE_NAME,
                         'dump_interval': self._re_params['dump_interval']}

        return updates

    def _setup_simulation(self, current_storage, schedule, previous_storage=None,
                          prod=False):
        '''
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
        '''
        if previous_storage is not None:
            setup_timesteps(current_storage, schedule, previous_storage)
            setup_initial_states(current_storage, schedule, previous_storage)

        config_dict = self._fill_config_template(
            current_storage, previous_storage, schedule, prod)
        current_storage.save_config(config_dict)
        current_storage.save_schedule(schedule)
        self._scale_environment(schedule_length(schedule))

    def _do_single_run(self, storage):
        '''
        Run a single Replica Exchange simulation, estimate the density of
        states and write it to the simulation folder.

        Args:
            storage(:class:`SimulationStorage`): storage for simulation
              to be set up

        Returns:
          :class:`np.array`: density of states estimate
        '''
        self._re_runner.run_sampling(storage)
        energies = storage.load_all_energies()
        schedule = storage.load_schedule()
        dos = self._dos_estimator.estimate_dos(energies, schedule)
        storage.save_dos(dos)

    def run_job(self):
        '''
        Runs a complete Replica Exchange sampling job.

        This comprises schedule optimization and a final production run.
        '''
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
