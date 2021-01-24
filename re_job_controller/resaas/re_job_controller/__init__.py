from abc import abstractmethod, ABC

import yaml
import numpy as np

from resaas.common.util import storage_factory
from resaas.schedule_estimation.dos_estimators import WHAM, BoltzmannEnsemble
from resaas.schedule_estimation.schedule_optimizers import SingleParameterScheduleOptimizer
from resaas.schedule_estimation.optimization_quantities import acceptance_rate


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


# I totally made up a word for "the one before the last one"
def optimization_converged(preprevious_schedule, previous_schedule):
    return schedule_length(preprevious_schedule) \
      == schedule_length(previous_schedule)


class InitialValueSetuper:
    def __init__(self, pickle_storage, string_storage):
        self.pickle_storage = pickle_storage
        self.string_storage = string_storage

    def _setup_timesteps(self, sim_path, schedule, previous_sim_path=None):
        if previous_sim_path is None:
            timesteps = np.linspace(1e-3, 1e-1, len(schedule))
        else:
            old_timesteps = self.pickle_storage.read(
                previous_sim_path + FINAL_TIMESTEPS_PATH)
            old_schedule = self.pickle_storage.read(
                previous_sim_path + SCHEDULE_PATH)
            timesteps = self.interpolate_timesteps(schedule, old_schedule,
                                                   old_timesteps)
        self.pickle_storage.write(timesteps,
                                  sim_path + TIMESTEPS_PATH)

    def _interpolate_timesteps(self, schedule, old_schedule, old_timesteps):
        # TODO: somehow interpolate timesteps from old simulation, e.g., by
        # fitting spline or just simple linear interpolation
        return np.array([0.001] * schedule_length(schedule))

    def _draw_initial_states(self, schedule, previous_sim_path, dos):
        # TODO: draw initial states using the DOS and previous states
        return np.array([0.001] * schedule_length(schedule))

    def setup_initial_states(self, sim_path, schedule, dos=None,
                             previous_sim_path=None):
        if previous_sim_path is not None:
            initial_states = self._draw_initial_states(schedule,
                                                       previous_sim_path,
                                                       dos)
            self.pickle_storage.write(initial_states,
                                      sim_path + INITIAL_STATES_PATH)


class AbstractInitialScheduleMaker(ABC):
    def __init__(self, param_name):
        self._param_name = param_name

    @abstractmethod
    def make_initial_schedule(self, **params):
        pass


class GeometricInitialScheduleMaker(AbstractInitialScheduleMaker):
    def make_initial_schedule(self, num_replicas, min_value, max_value=1.0):
        common_ratio = (max_value / min_value) ** (1. / num_replicas)
        geometric_progression = common_ratio ** np.arange(num_replicas)
        return {self._param_name: geometric_progression}


class AbstractREJobController(ABC):
    def __init__(self, job_spec, re_runner,
                 initial_schedule_maker=GeometricInitialScheduleMaker,
                 schedule_optimizer=SingleParameterScheduleOptimizer,
                 ensemble=BoltzmannEnsemble,
                 optimization_quantity=acceptance_rate,
                 dos_estimator=WHAM):
        self._re_runner = re_runner
        self._initial_schedule_maker = initial_schedule_maker
        self._schedule_optimizer = schedule_optimizer
        self._optimization_quantity = optimization_quantity
        self._dos_estimator = dos_estimator
        self._basename = job_spec['path']
        self._pickle_storage, self._string_storage = storage_factory(
            self._basename)
        self._initial_value_setuper = InitialValueSetuper(
            self._pickle_storage, self._string_storage)
        self._re_params = None
        self._local_sampling_params = None
        self._optimization_params = None
        self._set_params(job_spec)

    def _set_params(self, job_spec):
        self._re_params = job_spec['re_params']
        self._local_sampling_params = job_spec['local_sampling_params']
        self._optimization_params = job_spec['optimization_params']
        self._initial_schedule_params = job_spec['initial_schedule_params']

    @abstractmethod
    def _scale_environment(self, num_replicas):
        pass

    def optimize_schedule(self):
        run_counter = 0
        dos = None
        previous_schedule = None
        preprevious_schedule = None
        previous_sim_path = None
        opt_params = self._optimization_params
        while (not optimization_converged(preprevious_schedule,
                                          previous_schedule)
               or run_counter > opt_params['max_optimization_runs']):
            log('Schedule optimization simulation #{} started'.format(
                run_counter))
            sim_path = 'optimization_run{}/'.format(run_counter)
            if previous_schedule is not None:
                optimizer = self._schedule_optimizer(
                    dos, self._load_energies(previous_sim_path),
                    acceptance_rate)
                schedule = optimizer.optimize(
                    self._optimization_params['target_value'],
                    self._optimization_params['max_param'],
                    self._optimization_params['min_param'],
                    self._optimization_params['decrement'],)
            else:
                schedule = self._initial_schedule_maker.make_initial_schedule(
                    **self._initial_schedule_params)
            self._setup_simulation(sim_path, schedule, dos, previous_sim_path)
            dos = self._do_single_run(sim_path)

            previous_sim_path = sim_path
            preprevious_schedule = previous_schedule
            previous_schedule = schedule
            run_counter += 1
            if run_counter == opt_params['max_optimization_runs']:
                log(('Maximum number of optimization runs reached. '
                     'Schedule optimization might not have converged'))

        final_dos = self._dos_estimator.calculate_dos(schedule)
        final_schedule = self._schedule_optimizer.optimize(dos)

        return sim_path, final_schedule, final_dos

    def _fill_config_template(self, sim_path, previous_sim_path, schedule,
                              prod=False):
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
        updates['re'] = {'schedule': sim_path + SCHEDULE_PATH}

        return updates

    def _setup_simulation(self, sim_path, schedule, previous_dos=None,
                          previous_sim_path=None, prod=False):
        if previous_sim_path is None:
            self._initial_value_setuper.setup_timesteps(sim_path, schedule,
                                                        previous_sim_path)
            self._initial_value_setuper.setup_initial_states(
                sim_path, schedule, previous_dos, previous_sim_path)

        config_dict = self._fill_config_template(sim_path, schedule, prod)
        config = self._make_config_str(**config_dict)
        self._string_storage.write(config, sim_path + CONFIG_PATH,
                                   mode_flags='w')
        self._pickle_storage.write(schedule, sim_path + SCHEDULE_PATH)
        self._scale_environment(schedule_length(schedule))

    def _load_energies(self, sim_path):
        config = yaml.safe_load(self._string_storage.read(sim_path + CONFIG_PATH))
        n_replicas = config['general']['num_replicas']
        n_samples = config['general']['n_iterations']
        dump_interval = config['re']['dump_interval']
        energies = []
        for r in range(1, n_replicas + 1):
            r_energies = []
            for n in range(0, n_samples - dump_interval, dump_interval):
                fname = 'energies_replica{}_{}-{}.pickle'.format(
                    r, n, n + dump_interval)
                r_energies.append(self._pickle_storage.read(
                    sim_path + ENERGIES_PATH + fname))
            energies.append(np.concatenate(r_energies))
        return np.array(energies)

    def _do_single_run(self, sim_path):
        self._re_runner.run_sampling(sim_path)
        energies = self._load_energies(sim_path)
        schedule = self._pickle_storage.read(sim_path + SCHEDULE_PATH)
        dos_estimator = self._dos_estimator(energies, self._ensemble, schedule)
        dos = dos_estimator.estimate_dos()
        self._pickle_storage.write(dos, DOS_PATH)
        return dos

    def _check_compatibility(self, initial_schedule_params,
                             optimization_params):
        # TODO: check whether optimization params and initial schedule params
        # are compatible. Although that's a late failure - perhaps do this upon
        # job submission?
        pass

    def _make_config_str(self, **kwargs):
        cfg = cfg_template.copy()
        for key, value in kwargs.items():
            cfg[key].update(**value)
        return yaml.dump(cfg)

    def run_job(self):
        self._check_compatibility(self._initial_schedule_params,
                                  self._optimization_params)

        optimization_result = self._optimize_schedule()
        final_opt_sim_path, final_schedule, final_dos = optimization_result

        self._setup_simulation(PROD_OUTPUT_PATH, final_schedule, final_dos,
                               final_opt_sim_path, prod=True)
        self._do_single_run(PROD_OUTPUT_PATH)


class LocalREJobController(AbstractREJobController):
    def _scale_environment(self, _):
        pass


job_spec = dict(re_params=dict(num_replicas=8, num_optimization_samples=5000),
                local_sampling_params=dict(hmc_num_adaption_steps=100),
                optimization_params=dict(target_value=0.3, max_param=1,
                                         min_param=0.1, decrement=0.05),
                initial_schedule_params=dict(beta_min=0.01, beta_ratio=0.9),
                path='/tmp/jctest/')

c = REJobController(job_spec, MockRERunner())
c.run_job()
