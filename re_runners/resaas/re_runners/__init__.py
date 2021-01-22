from abc import abstractmethod, ABCMeta
import os

import yaml


from resaas.common.util import storage_factory

class AbstractRERunner(metaclass=ABCMeta):
    @abstractmethod
    def run_sampling(self, config_file):
        pass


class MPIRERunner(AbstractRERunner):
    def run_sampling(self, config_file):
        _, string_storage = storage_factory('/tmp/jctest/')
        config = yaml.load(string_storage.read(config_file))
        n_replicas = config['general']['num_replicas']
        cfg_path = config['general_params']['output_path'] + 'config.yml'
        output = os.subprocess.check_output([
            'mpirun', '-n', str(n_replicas + 1),
            'python', 'run_simulation.py', cfg_path, "local"])
