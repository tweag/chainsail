"""
Classes which allow writing out stuff (samples, energies, ...) to
different locations (local file systems, cloud storage, ...)
"""
import os
from abc import ABC, abstractmethod
from collections import namedtuple
from io import BytesIO, StringIO
from pickle import dump, load

import numpy as np
import yaml
from libcloud.storage.providers import get_driver
from libcloud.storage.types import Provider
from marshmallow import Schema, fields
from marshmallow.decorators import post_load

dir_structure = dict(
    SAMPLES_TEMPLATE="samples/samples_{}_{}-{}.pickle",
    ENERGIES_TEMPLATE="energies/energies_{}_{}-{}.pickle",
    INITIAL_TIMESTEPS_FILE_NAME="initial_timesteps.pickle",
    FINAL_TIMESTEPS_FILE_NAME="final_timesteps.pickle",
    INITIAL_STATES_FILE_NAME="initial_states.pickle",
    DOS_FILE_NAME="dos.pickle",
    SCHEDULE_FILE_NAME="schedule.pickle",
    CONFIG_FILE_NAME="config.yml",
)
DirStructure = namedtuple("DirStructure", dir_structure)
default_dir_structure = DirStructure(**dir_structure)


def make_sure_basename_exists(file_path):
    """Makes sure the basename of a file path exists.

    TODO: log warning if it does.

    Args:
      file_path: a (possibly relative) file path
    """
    os.makedirs(file_path[: file_path.rfind("/")], exist_ok=True)


def pickle_to_stream(obj):
    """Pickles a Python object and writes it to a BytesIO stream.

    Args:
      obj(object): some pickleable Python object

    Returns:
      BytesIO: byte stream with pickled object
    """
    bytes_stream = BytesIO()
    dump(obj, bytes_stream)
    bytes_stream.seek(0)
    return bytes_stream


def load_storage_backend(backend_name: str, backend_config: dict):
    """Loads a storage backend using the provided config.

    Args:
        backend_name: The name of the backend. See `BACKEND_SCHEMA_REGISTRY`. For
            available options.
        backend_config: The parameters required to load the specific backend. See
            the schemas in `BACKEND_SCHEMA_REGISTRY` for a list of configs.

    Raises:
        Exception: If the backend cloud not be loaded
    """
    if backend_name == "local":
        return LocalStorageBackend()
    elif backend_name == "cloud":
        try:
            provider = getattr(Provider, backend_config["libcloud_provider"])
        except AttributeError:
            raise Exception(
                f"Unrecognized libcloud provider: {backend_config['libcloud_provider']}. "
                "See libcloud.storage.types.Provider for a full list of available options."
            )
        driver_cls = get_driver(provider)
        driver = driver_cls(**backend_config["driver_kwargs"])
        container = driver.get_container(container_name=backend_config["container_name"])
        return CloudStorageBackend(driver, container)
    else:
        raise Exception(f"Unrecognized storage backend name: '{backend_name}'.")


def load_storage_config(config_file: str) -> "StorageBackendConfig":
    """Loads storage backend configuration from a YAML config file

    Args:
        config_file: The path to the config file
    """
    with open(config_file) as f:
        return StorageBackendConfigSchema().load(yaml.load(f))


class LocalBackendConfigSchema(Schema):
    # Local backend requires no config :)
    pass


class CloudBackendConfigSchema(Schema):
    libcloud_provider = fields.String(required=True)
    container_name = fields.String(required=True)
    driver_kwargs = fields.Dict(fields.String, fields.String, required=True)

    @post_load
    def make_backend(self, data, **kwargs) -> "CloudStorageBackend":
        return CloudStorageBackend()


# Registry used for looking up schema during deserialization
BACKEND_SCHEMA_REGISTRY = {"local": LocalBackendConfigSchema, "cloud": CloudBackendConfigSchema}


class StorageBackendConfigSchema(Schema):
    backend = fields.String(required=True)
    backend_config = fields.Dict(fields.String, fields.Dict, required=True)

    @post_load
    def make_backend(self, data, **kwargs) -> "AbstractStorageBackend":
        # Look up the desired backend and attempt to parse its config
        try:
            schema = BACKEND_SCHEMA_REGISTRY[data["backend"]]()
        except KeyError:
            # TODO: Add a custom exception type here
            raise Exception(f"Unrecognized backend: '{data['backend']}'")
        try:
            specified_config = data["backend_config"][data["backend"]]
        except KeyError:
            raise Exception(
                "Did not specify the storage_backend's corresponding config: "
                f"'{data['backend']}'"
            )
        backend_config = schema.load(specified_config)
        return StorageBackendConfig(data["backend"], backend_config)


class StorageBackendConfig:
    """Configuration for storage backlends

    Args:
        backend: The backend name. See `BACKEND_SCHEMA_REGISTRY` for a list of available options.
        backend_config: The backend's config
    """

    def __init__(
        self,
        backend: str,
        backend_config: dict,
    ):
        self.backend = backend
        self.backend_config = backend_config

    def get_storage_backend(self) -> "AbstractStorageBackend":
        """Create a new storage backend instance using the controller config"""
        return load_storage_backend(self.backend, self.backend_config)


class AbstractStorageBackend(ABC):
    @abstractmethod
    def write(self, data, file_name):
        """Write data to some kind of permanent storage.

        Args:
          data(object): data to write
          **kwargs:

        Returns:

        """
        pass

    @abstractmethod
    def load(self, file_name, data_type="pickle"):
        pass


class LocalStorageBackend(AbstractStorageBackend):
    def write(self, data, file_name):
        make_sure_basename_exists(file_name)
        if type(data) == str:
            with open(file_name, "w") as f:
                f.write(data)
        else:
            with open(file_name, "wb") as f:
                dump(data, f)

    def load(self, file_name, data_type="pickle"):
        if data_type == "pickle":
            with open(file_name, "rb") as f:
                return load(f)
        if data_type == "text":
            with open(file_name, "r") as f:
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
        stringio.write(str(chunk, "ascii"))
    stringio.seek(0)

    return stringio


class CloudStorageBackend(AbstractStorageBackend):
    def __init__(self, driver, container):
        """Cloud storage backend.

        Uses ``libcloud`` to work with different cloud providers.

        driver: libcloud driver instance
        container: libcloud container
        """
        self._driver = driver
        self._container = container

    def write(self, data, file_name, data_type="pickle"):
        if data_type == "text":
            stream = StringIO(data)
        elif data_type == "pickle":
            stream = pickle_to_stream(data)
        else:
            raise ValueError("'data_type' has to be either 'text' or 'pickle'")
        self._driver.upload_object_via_stream(stream, self._container, file_name)

    def load(self, file_name, data_type="pickle"):
        obj = self._driver.get_object(self._container.name, file_name)
        stream = self._driver.download_object_as_stream(obj)
        # TODO: all this stream business stinks
        if data_type == "pickle":
            return load(bytes_iterator_to_bytesio(stream))
        elif data_type == "text":
            return bytes_iterator_to_stringio(stream).read()
        else:
            raise ValueError("'data_type' has to be either 'text' or 'pickle'")


class SimulationStorage:
    def __init__(self, basename, sim_path, storage_backend, dir_structure=default_dir_structure):
        self._basename = basename
        self._sim_path = sim_path
        self._storage_backend = storage_backend
        self._dir_structure = dir_structure

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
        return os.path.join(self._basename, self._sim_path, self.dir_structure.CONFIG_FILE_NAME)

    @property
    def dir_structure(self):
        return self._dir_structure

    def save(self, data, file_name, data_type="pickle"):
        self._storage_backend.write(
            data, os.path.join(self._basename, self.sim_path, file_name), data_type
        )

    def load(self, file_name, data_type="pickle"):
        return self._storage_backend.load(
            os.path.join(self._basename, self.sim_path, file_name), data_type
        )

    def save_samples(self, samples, replica_name, from_samples, to_samples):
        self.save(
            samples,
            self.dir_structure.SAMPLES_TEMPLATE.format(replica_name, from_samples, to_samples),
        )

    def save_energies(self, energies, replica_name, from_energies, to_energies):
        self.save(
            energies,
            self.dir_structure.ENERGIES_TEMPLATE.format(replica_name, from_energies, to_energies),
        )

    def load_energies(self, replica_name, from_energies, to_energies):
        return self.load(
            self.dir_structure.ENERGIES_TEMPLATE.format(replica_name, from_energies, to_energies)
        )

    def load_all_energies(self):
        config = self.load_config()
        n_replicas = config["general"]["num_replicas"]
        n_samples = config["general"]["n_iterations"]
        dump_interval = config["re"]["dump_interval"]
        energies = []
        for r in range(1, n_replicas + 1):
            r_energies = []
            for n in range(0, n_samples - dump_interval, dump_interval):
                energies_batch = self.load_energies("replica" + str(r), n, n + dump_interval)
                r_energies.append(energies_batch)
            energies.append(np.concatenate(r_energies))
        return np.array(energies)

    def save_config(self, config_dict):
        self.save(yaml.dump(config_dict), self.dir_structure.CONFIG_FILE_NAME, data_type="text")

    def load_config(self):
        return yaml.safe_load(self.load(self.dir_structure.CONFIG_FILE_NAME, data_type="text"))

    def save_dos(self, dos):
        self.save(dos, self.dir_structure.DOS_FILE_NAME)

    def load_dos(self):
        return self.load(self.dir_structure.DOS_FILE_NAME)

    def save_schedule(self, schedule):
        self.save(schedule, self.dir_structure.SCHEDULE_FILE_NAME)

    def load_schedule(self):
        return self.load(self.dir_structure.SCHEDULE_FILE_NAME)

    def save_initial_timesteps(self, timesteps):
        self.save(timesteps, self.dir_structure.INITIAL_TIMESTEPS_FILE_NAME)

    def load_initial_timesteps(self):
        return self.load(self.dir_structure.INITIAL_TIMESTEPS_FILE_NAME)

    def save_final_timesteps(self, timesteps):
        self.save(timesteps, self.dir_structure.FINAL_TIMESTEPS_FILE_NAME)

    def load_final_timesteps(self):
        return self.load(self.dir_structure.FINAL_TIMESTEPS_FILE_NAME)

    def save_initial_states(self, initial_states):
        self.save(initial_states, self.dir_structure.INITIAL_STATES_FILE_NAME)

    def load_initial_states(self):
        return self.load(self.dir_structure.INITIAL_STATES_FILE_NAME)
