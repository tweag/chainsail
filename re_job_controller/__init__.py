from abc import abstractmethod, ABCMeta
from pickle import dump
from io import BytesIO, StringIO

from libcloud.storage.base import Object, Container

from helpers import create_helpers
from env_helpers import driver_factory
from job_helpers import container_factory


class REJobController:
    def __init__(self, re_runner):
        self.re_runner = re_runner
        self.dos_calculator = None
        self.schedule_optimizer = None
        self.initial_schedule_calculator = None

    def _set_helpers(self, initial_schedule_params, optimization_params):
        helpers = create_helpers(initial_schedule_params, optimization_params)
        self.dos_calculator, self.scheduler_optimizer, self.initial_schedule \
            = helpers

    def push_to_storage(self, obj, name):
        pass

    def log_result(self):
        pass
    
    def optimize_schedule(self, initial_schedule_params, max_optimization_runs,
                          initial_local_params, re_params):
        run_counter = 0
        dos = None
        schedule = None
        previous_sim_path = None
        while (not self.optimization_converged()
               or run_counter > max_optimization_runs):
            sim_path = 'optimization_run{}/'.format(run_counter)
            if schedule is not None:
                schedule = self.schedule_optimizer.optimize(dos)
                self.scale_environment(self.schedule.length)
            else:
                schedule = self.make_initial_schedule(initial_schedule_params,
                                                      re_params['num_replicas'])
            self.setup_initial_values(sim_path, schedule, dos,
                                      previous_sim_path)
            dos = self.do_single_run()
            previous_sim_path = sim_path
            run_counter += 1

        final_dos = self.dos_calculator.calculate_dos(schedule)
        final_schedule = self.schedule_optimizer.optimize(dos)

        return sim_path, final_schedule, final_dos

    def setup_simulation(self, sim_path, schedule, config, dos=None,
                         sampling_result=None):
        schedule_stream = BytesIO()
        dump(schedule, schedule_stream)
        self.push_to_storage(schedule_stream, sim_path + 'schedule.pickle')
        initial_states = self.draw_initial_states(dos, sampling_result)
        initial_states_stream = BytesIO()
        dump(initial_states, initial_states_stream)
        self.push_to_storage(initial_states_stream,
                             sim_path + 'initial_states.pickle')
        local_sampling_params = self.determine_local_sampling_params(
            sampling_result)
        local_sampling_params_stream = BytesIO()
        dump(local_sampling_params, local_sampling_params_stream)
        self.push_to_storage(local_sampling_params_stream,
                             sim_path + 'local_sampling_params.pickle')
        global_config_stream = StringIO(self.dict_to_cfg_string(config))
        self.push_to_storage(global_config_stream, sim_path + 'config.yml')

    def do_single_run(self, sim_path, schedule, config, previous_dos=None,
                      previous_sim_path=None):
        env_info = self.scale_environment(parameter_set['schedule'].length)
        self.setup_initial_values(sim_path, schedule, config, dos=None,
                                  sampling_result=None)
        self.re_runner.run_sampling()
        dos = self.dos_calculator.calculate_dos(schedule)
        dos_stream = BytesIO()
        dump(dos, dos_stream)
        self.push_to_storage(dos_stream, 'dos_estimate.pickle')

        return dos

    def check_compatibility(self, initial_schedule_params, optimization_params):
        pass

    def make_config(self):
        cfg_dict = {
            re_params = {
                'n_iterations': 5000,
                'swap_interval': 5,
                'status_interval': 100,
                'dump_interval': 1000,
                'dump_step': 1,
                'statistics_update_interval': 50,
                'offset': 0
            }
        }

    def run_job(self, job_spec, env_info):
        self.job_spec = job_spec
        self.env_info = env_info
        self.check_compatibility(job_spec['initial_schedule_params'],
                                 job_spec['optimization_params'])
        self._set_helpers(job_spec['initial_schedule_params'],
                          job_spec['optimization_params'])

        final_opt_sim_path, final_schedule, final_dos = self.optimize_schedule(
            job_spec['initial_schedule_params'],
            job_spec['optimization_params']['max_optimization_runs'],
            job_spec['initial_local_params'], job_spec['re_params'])
        prod_config = self.make_config(re_params=job_spec['prod_re_params'])
        self.setup_simulation('production_run/', final_schedule, prod_config,
                              final_dos, final_opt_sim_path)
        self.do_single_run()
        self.log_result()
