from libcloud.storage.base import Object, Container

from helpers import create_helpers
from env_helpers import driver_factory
from job_helpers import container_factory


class FullParameterSet:
    def __init__(self, container, driver, **items):
        self._items = items

    def __setitem__(self, key, value):
        self._items[key] = value

    def __getitem__(self, key):
        obj = Object(self._items[key])
        return self.driver.download_object_as_stream(obj)


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

    def make_parameter_set(self, **params):
        container = Container(self.job_spec['container_name'])
        driver = self.env_info['driver']
        return FullParameterSet(container, driver, **params)
        
    def optimize_schedule(self, initial_schedule_params, max_optimization_runs,
                          initial_local_params, re_params, initial_states):
        parameter_set = self.make_initial_parameter_set(
            initial_schedule_params, max_optimization_runs,
            initial_local_params, re_params, initial_states)

        run_counter = 0
        while (not self.optimization_converged()
               or run_counter > max_optimization_runs):
            env_info = self.scale_environment(self.schedule.length)
            sampling_result = self.re_runner.run_sampling(env_info,
                                                          parameter_set)
            dos = self.dos_calculator.calculate_dos(
                sampling_result, parameter_set['pdf'].log_prob)
            schedule = self.schedule_optimizer.optimize(dos)
            initial_states, local_params = self.setup_initial_values(
                dos, sampling_result, schedule)
            parameter_set = FullParameterSet(schedule, initial_states,
                                             local_params, re_params)
            run_counter += 1

        return parameter_set

    def make_initial_parameter_set(self, job_spec):
        schedule = self.initial_schedule_calculator.calculate_schedule(
            job_spec['initial_schedule_params']
        )
        initial_parameter_set = FullParameterSet(
            schedule, job_spec['initial_states_params'],
            job_spec['initial_local_params'], job_spec['re_params'])
        return initial_parameter_set

    def do_single_run(self, parameter_set):
        env_info = self.scale_environment(parameter_set['schedule'].length)
        sampling_result = self.re_runner.run_sampling(env_info,
                                                      parameter_set)
        dos = self.dos_calculator.calculate_dos(
            sampling_result, parameter_set['probability_definition'])

        return SingleRunResult(sampling_result, dos)

    def run_job(self, job_spec, env_info):
        self.job_spec = job_spec
        self.env_info = env_info
        self.check_compatibility(job_spec['initial_schedule_params'],
                                 job_spec['optimization_params'])
        self._set_helpers(job_spec['initial_schedule_params'],
                          job_spec['optimization_params'])
        initial_parameter_set = self.make_initial_parameter_set(job_spec)
        optimized_parameter_set = self.optimize_schedule(initial_parameter_set)
        final_result = self.do_single_run(optimized_parameter_set)
        self.log_result(final_result)

        return final_result
