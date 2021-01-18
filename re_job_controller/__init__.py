from abc import ABCMeta
import pickle

import yaml
import numpy as np

from storage import (FileSystemPickleStorage,
                     # CloudPickleStorage,
                     FileSystemStringStorage,
                     # CloudStringStorage
                     )
from dos_calculators import BoltzmannDOSCalculator
from schedule_optimizers import BoltzmannAcceptanceRateOptimizer

TIMESTEPS_PATH = 'timesteps.pickle'
FINAL_TIMESTEPS_PATH = 'final_timesteps.pickle'
INITIAL_STATES_PATH = 'initial_states.pickle'
DOS_PATH = 'dos.pickle'
FINAL_DOS_PATH = 'final_dos.pickle'
SCHEDULE_PATH = 'schedule.pickle'

cfg_template = {
    're_params': {
        'n_iterations': None,
        'swap_interval': 5,
        'status_interval': 100,
        'dump_interval': 1000,
        'statistics_update_interval': 50,
    },
    'general_params': {
        'output_path': None
    },
    'local_sampling_params': {
        'n_steps': 20,
        'timesteps': None,
        'timestep_adaption_limit': None,
        'adaption_uprate': 1.05,
        'adaption_downrate': 0.95,
        'initial_states': None
    }
}


def storage_factory(path):
    pstorage = FileSystemPickleStorage(path)
    sstorage = FileSystemStringStorage(path)
    return pstorage, sstorage


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
        while (not self.optimization_converged()
               or run_counter > self.optimization_params['max_optimization_runs'):
            sim_path = 'optimization_run{}/'.format(run_counter)
            if schedule is not None:
                schedule = self.schedule_optimizer.optimize(dos)
            else:
                schedule = self.make_initial_schedule(
                    self.initial_schedule_params, re_params['num_replicas'])
            self.setup_simulation(sim_path, schedule, config, dos,
                                  previous_sim_path)
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
            config_updates['local_sampling_params'] = {
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
        config = self.make_config(general={'output_path': sim_path},
                                  **config_updates)
        self.storage.write(config, sim_path + 'config.yml')
        self.scale_environment(get_schedule_length(schedule))

    def do_single_run(self, sim_path):
        self.re_runner.run_sampling()
        dos = self.dos_calculator.calculate_dos(schedule)
        self.storage.write(dos, DOS_PATH)
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

        prod_output_path = 'production_run/'
        self.setup_simulation(prod_output_path, final_schedule, final_dos,
                              final_opt_sim_path, prod=True)
        self.do_single_run(prod_output_path)
        self.log_result()
