'''
Runners which launch a rexfw simulation in different deployments.
'''
from abc import abstractmethod, ABC
import os
from subprocess import check_output


def get_run_script_path():
    return check_output(['which', 'run_simulation']).strip()


class AbstractRERunner(ABC):
    @abstractmethod
    def run_sampling(self, storage):
        pass


class MPIRERunner(AbstractRERunner):
    def run_sampling(self, storage):
        config = storage.load_config_file()
        n_replicas = config['general']['num_replicas']
        cfg_path = os.path.join(storage.basename, storage.sim_path,
                                storage.dir_structure.CONFIG_FILE_NAME)
        mpirun_args = ['--oversubscribe', '-n', str(n_replicas + 1)]
        run_script_args = [cfg_path, "local"]
        output = check_output(['mpirun'] + mpirun_args +
                              ["python", get_run_script_path()]
                              + run_script_args)
