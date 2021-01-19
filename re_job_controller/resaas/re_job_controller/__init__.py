from abc import ABCMeta
import pickle

import yaml
import numpy as np

from resaas.lib.util import storage_factory
from resaas.schedule_estimation.dos_calculators import BoltzmannDOSCalculator
from resaas.schedule_estimation.schedule_optimizers import BoltzmannAcceptanceRateOptimizer

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
    're_params': {
        'n_iterations': None,
        'swap_interval': 5,
        'status_interval': 100,
        'dump_interval': 1000,
        'statistics_update_interval': 50,
    },
    'general_params': {
        'output_path': None,
        'initial_states': None,
        'num_replicas': None
    },
    'local_sampling_params': {
        'n_steps': 20,
        'timesteps': None,
        'timestep_adaption_limit': None,
        'adaption_uprate': 1.05,
        'adaption_downrate': 0.95,
    }
}


def get_schedule_length(schedule):
    return len(list(schedule.values())[0])


class InitialValueSetuper(metaclass=ABCMeta):
    def __init__(self, pickle_storage, string_storage):
        self.pickle_storage = pickle_storage
        self.string_storage = string_storage

    def setup_timesteps(self, sim_path, schedule, previous_sim_path=None):
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

    def interpolate_timesteps(self, schedule, old_schedule, old_timesteps):
        # TODO
        return np.array([0.001] * get_schedule_length(schedule))

    def setup_initial_states(self, sim_path, schedule, dos=None,
                             previous_sim_path=None):
        if previous_sim_path is not None:
            initial_states = self.draw_initial_states(schedule,
                                                      previous_sim_path,
                                                      dos)
            self.pickle_storage.write(initial_states,
                                      sim_path + INITIAL_STATES_PATH)


class REJobController:
    def __init__(self, job_spec, re_runner, storage):
        self.re_runner = re_runner
        self.dos_calculator = BoltzmannDOSCalculator
        self.schedule_optimizer = BoltzmannAcceptanceRateOptimizer()
        self.initial_schedule_calculator = None
        self.pickle_storage, self.string_storage = storage_factory(
            job_spec(['job_name']))
        self.re_params = None
        self.local_sampling_params = None
        self.optimization_params = None
        self._set_params(job_spec)

    def _set_params(self, job_spec):
        self.re_params = job_spec['re_params']
        self.local_sampling_params = job_spec['local_sampling_params']
        self.optimization_params = job_spec['optimization_params']

    def _set_helpers(self, initial_schedule_params, optimization_params):
        helpers = create_helpers(initial_schedule_params, optimization_params)
        self.dos_calculator, self.scheduler_optimizer, self.initial_schedule \
            = helpers

    def log_result(self):
        pass

    def make_initial_schedule(self, params, num_replicas):
        schedule = [1.0]
        while schedule[-1] > params['beta_min']:
            schedule.append(schedule[-1] * params['beta_ratio'])
        schedule.append(params['beta_min'])
        if len(schedule) > num_replicas:
            # TODO
            schedule = schedule[:num_replicas]
        return {'beta': np.array(schedule)}

    def optimize_schedule(self):
        run_counter = 0
        dos = None
        schedule = None
        previous_sim_path = None
        opt_params = self.optimization_params
        while (not self.optimization_converged()
               or run_counter > opt_params['max_optimization_runs']):
            sim_path = 'optimization_run{}/'.format(run_counter)
            if schedule is not None:
                schedule = self.schedule_optimizer.optimize(dos)
            else:
                schedule = self.make_initial_schedule(
                    self.initial_schedule_params,
                    self.re_params['num_replicas'])
            self.setup_simulation(sim_path, schedule, dos, previous_sim_path)
            dos = self.do_single_run()
            previous_sim_path = sim_path
            run_counter += 1

        final_dos = self.dos_calculator.calculate_dos(schedule)
        final_schedule = self.schedule_optimizer.optimize(dos)

        return sim_path, final_schedule, final_dos

    def setup_simulation(self, sim_path, schedule, previous_dos=None,
                         previous_sim_path=None, prod=False):
        config_updates = {}
        if previous_sim_path is not None:
            self.initial_value_setuper.setup_timesteps(sim_path, schedule,
                                                       previous_sim_path)
            config_updates['local_sampling_params'] = {
                'timesteps': sim_path + TIMESTEPS_PATH}
            self.initial_value_setuper.setup_initial_states(sim_path, schedule,
                                                            previous_dos,
                                                            previous_sim_path)
            config_updates['general'] = {
                'initial_states': sim_path + INITIAL_STATES_PATH}
        if prod:
            num_samples = self.re_params['num_production_samples']
        else:
            num_samples = self.re_params['num_optimization_samples']
        config_updates['re_params'] = {'n_iterations': num_samples}
        ts_adaption_limit = self.local_sampling_params['hmc_num_adaption_steps'] \
            or int(0.1 * num_samples)
        config_updates['local_sampling_params']['timestep_adaption_limit'] = \
            ts_adaption_limit
        n_replicas = get_schedule_length(schedule)
        config = self.make_config(general={'output_path': sim_path,
                                           'num_replicas': n_replicas},
                                  **config_updates)
        self.string_storage.write(config, sim_path + CONFIG_PATH)
        self.scale_environment(get_schedule_length(schedule))

    def load_energies(self, sim_path):
        config = yaml.load(self.string_storage.read(sim_path + CONFIG_PATH))
        n_replicas = config['general_params']['num_replicas']
        n_samples = config['general_params']['num_iterations']
        dump_interval = config['re_params']['dump_interval']
        energies = []
        for r in range(1, n_replicas + 1):
            r_energies = []
            for n in range(0, n_samples - dump_interval, dump_interval):
                fname = 'energies_replica{}_{}-{}.pickle'.format(
                    r, n, n + dump_interval)
                r_energies.append(self.pickle_storage.load(
                    sim_path + ENERGIES_PATH + fname))
        return np.array(energies)
        
    def do_single_run(self, sim_path):
        self.re_runner.run_sampling()
        energies = self.load_energies(sim_path)
        schedule = self.pickle_storage.read(SCHEDULE_PATH)
        dos = self.dos_calculator.calculate_dos(energies, schedule)
        self.pickle_storage.write(dos, DOS_PATH)
        return dos

    def check_compatibility(self, initial_schedule_params,
                            optimization_params):
        # TODO
        pass

    def make_config(self, **kwargs):
        cfg = cfg_template.copy()
        for key, value in kwargs.items():
            cfg[key].update(**value)
        return yaml.dump(cfg)

    def run_job(self):
        self.check_compatibility(self.initial_schedule_params,
                                 self.optimization_params)

        optimization_result = self.optimize_schedule()
        final_opt_sim_path, final_schedule, final_dos = optimization_result

        self.setup_simulation(PROD_OUTPUT_PATH, final_schedule, final_dos,
                              final_opt_sim_path, prod=True)
        self.do_single_run(PROD_OUTPUT_PATH)
        self.log_result()
