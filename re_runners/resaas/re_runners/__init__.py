'''
Runners which launch a rexfw simulation in different deployments.
'''
from abc import abstractmethod, ABC
import os
from subprocess import check_output

import yaml

# TODO: make adding `resaas.common` as a path dependency work
import sys
sys.path.append(os.getenv('RESAAS_COMMON_PATH'))

from resaas.common.util import storage_factory


def get_run_script_path():
    return check_output(['which', 'run_simulation']).strip()


class AbstractRERunner(ABC):
    @abstractmethod
    def run_sampling(self, config_file, basename):
        pass


class MPIRERunner(AbstractRERunner):
    def run_sampling(self, config_file, basename):
        _, string_storage = storage_factory(basename)
        config = yaml.load(string_storage.read(config_file))
        n_replicas = config['general']['num_replicas']
        cfg_path = config['general']['output_path'] + 'config.yml'
        cfg_path = basename + cfg_path
        mpirun_args = ['--oversubscribe', '-n', str(n_replicas + 1)]
        run_script_args = [cfg_path, "local"]
        output = check_output(['mpirun'] + mpirun_args +
                              ["python", get_run_script_path()]
                              + run_script_args)
