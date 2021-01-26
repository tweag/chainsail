'''
Classes which allow writing out stuff (samples, energies, ...) to
different locations (local file systems, cloud storage, ...)
'''
import os
from io import BytesIO, StringIO
from abc import abstractmethod, ABC
from pickle import dump, load
from enum import Enum

import yaml
import numpy as np


class DirStructure(Enum):
    SAMPLES_TEMPLATE = 'samples/samples_{}_{}-{}.pickle'
    ENERGIES_TEMPLATE = 'energies/energies_{}_{}-{}.pickle'
    INITIAL_TIMESTEPS_FILE_NAME = 'initial_timesteps.pickle'
    FINAL_TIMESTEPS_FILE_NAME = 'final_timesteps.pickle'
    INITIAL_STATES_FILE_NAME = 'initial_states.pickle'
    DOS_FILE_NAME = 'dos.pickle'
    CONFIG_FILE_NAME = 'config.yml'


def make_sure_basename_exists(file_path):
    '''Makes sure the basename of a file path exists.

    TODO: log warning if it does.

    Args:
      file_path: a (possibly relative) file path
    '''
    os.makedirs(file_path[:file_path.rfind('/')], exist_ok=True)


def pickle_to_stream(obj):
    '''Pickles a Python object and writes it to a BytesIO stream.

    Args:
      obj(object): some pickleable Python object

    Returns:
      BytesIO: byte stream with pickled object
    '''
    bytes_stream = BytesIO()
    dump(obj, bytes_stream)
    bytes_stream.seek(0)
    return bytes_stream


class AbstractStorageBackend(ABC):
    @abstractmethod
    def write(self, data, file_name):
        '''Write data to some kind of permanent storage.

        Args:
          data(object): data to write
          **kwargs: 

        Returns:

        '''
        pass

    @abstractmethod
    def load(self, file_name, data_type='pickle'):
        pass


class LocalStorageBackend(AbstractStorageBackend):
    def write(self, data, file_name):
        if type(data) == str:
            with open(file_name, 'w') as f:
                f.write(data)
        else:
            with open(file_name, 'wb') as f:
                dump(data, f)

    def load(self, file_name, data_type='pickle'):
        if data_type == 'pickle':
            with open(file_name, 'rb') as f:
                return load(f)
        if data_type == 'text':
            with open(file_name, 'r') as f:
                return f.read()


def bytes_iterator_to_bytesio(stream):
    bytesio = BytesIO()
    for chunk in stream:
        bytesio.write(chunk)
    bytesio.seek(0)

    return bytesio


def bytes_iterator_to_stringio(stream):
    stringio = StringIO()
    for chunk in stream:
        stringio.write(str(chunk, 'ascii'))
    stringio.seek(0)

    return stringio


class CloudStorageBackend(AbstractStorageBackend):
    def __init__(self, driver, container):
        '''Cloud storage backend.

        Uses ``libcloud`` to work with different cloud providers.

        driver: libcloud driver instance
        container: libcloud container
        '''
        self._driver = driver
        self._container = container

    def write(self, data, file_name):
        byte_data = pickle_to_stream(data)
        self._driver.upload_object_via_stream(
            byte_data, self._container, file_name)

    def read(self, file_name, data_type='pickle'):
        stream = self._driver.download_object_as_stream(file_name)
        # TODO: all this stream business stinks
        if data_type == 'pickle':
            return load(bytes_iterator_to_bytesio(stream))
        elif data_type == 'text':
            return bytes_iterator_to_stringio(stream).read()
        else:
            raise ValueError("'data_type' has to be either 'text' or 'pickle'")


class SimulationStorage:
    def __init__(self, basename, sim_path, storage_backend):
        self._basename = basename
        self._sim_path = sim_path
        self._storage_backend

    @property
    def basename(self):
        return self._basename

    @property
    def sim_path(self):
        return self._sim_path

    @sim_path.setter
    def sim_path(self, value):
        # TODO: sanitize / check
        self._sim_path = value

    @property
    def config_file_name(self):
        return os.join(self._basename, self._sim_path,
                       DirStructure.CONFIG_FILE_NAME)

    def save(self, data, file_name, data_type='pickle'):
        self._storage_backend.write(data, os.path.join(
            self._basename, file_name), data_type)

    def load(self, file_name):
        self._storage_backend.load(os.path.join(self._basename, file_name))

    def save_samples(self, samples, replica_name, from_samples, to_samples):
        self.save(samples, DirStructure.SAMPLES_TEMPLATE.format(
            replica_name, from_samples, to_samples))

    def save_energies(self, energies, replica_name, from_energies,
                      to_energies):
        self.save(energies, DirStructure.ENERGIES_TEMPLATE.format(
            replica_name, from_energies, to_energies))

    def load_energies(self, replica_name, from_energies, to_energies):
        return self.load(DirStructure.ENERGIES_TEMPLATE.format(
            replica_name, from_energies, to_energies))

    def load_all_energies(self):
        config = self.load_config(DirStructure.CONFIG_FILE_NAME)
        n_replicas = config['general']['num_replicas']
        n_samples = config['general']['n_iterations']
        dump_interval = config['re']['dump_interval']
        energies = []
        for r in range(1, n_replicas + 1):
            r_energies = []
            for n in range(0, n_samples - dump_interval, dump_interval):
                energies_batch = self.load_energies(
                    'replica' + str(r), n, n + dump_interval)
                r_energies.append(energies_batch)
            energies.append(np.concatenate(r_energies))
        return np.array(energies)

    def save_config(self, config_dict):
        self.save(yaml.dump(config_dict), DirStructure.CONFIG_FILE_NAME)

    def load_config(self):
        return yaml.safe_load(self.load(DirStructure.CONFIG_FILE_NAME),
                              data_type='text')

    def save_dos(self, dos):
        self.save(dos, DirStructure.DOS_FILE_NAME)

    def load_dos(self):
        return self.load(DirStructure.DOS_FILE_NAME)

    def save_initial_timesteps(self, timesteps):
        self.save(timesteps, DirStructure.INITIAL_TIMESTEPS_FILE_NAME)

    def load_initial_timesteps(self):
        return self.load(DirStructure.INITIAL_TIMESTEPS_FILE_NAME)

    def save_final_timesteps(self, timesteps):
        self.save(timesteps, DirStructure.FINAL_TIMESTEPS_FILE_NAME)

    def load_final_timesteps(self):
        return self.load(DirStructure.FINAL_TIMESTEPS_FILE_NAME)

    def save_initial_states(self, initial_states):
        self.save(initial_states, DirStructure.INITIAL_STATES_FILE_NAME)

    def load_initial_states(self):
        return self.load(DirStructure.INITIAL_STATES_FILE_NAME)
