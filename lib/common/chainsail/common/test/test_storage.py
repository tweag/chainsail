import os
import unittest
from pickle import dump, load
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np
from chainsail.common.storage import (
    LocalStorageBackend,
    SimulationStorage,
    pickle_to_stream,
)

obj = ["a", "list", 42]


LOCAL_STORAGE_CONFIG = {"backend": "local", "backend_config": {"local": {}}}
CLOUD_STORAGE_CONFIG = {
    "backend": "cloud",
    "backend_config": {
        "local": {},
        "cloud": {
            "libcloud_provider": "S3",
            "container_name": "foobar",
            "driver_kwargs": {"key": "xxxxxxxxxx"},
        },
    },
}


class MockStorageBackend:
    def __init__(self):
        self.data = {}

    def write(self, data, file_name, data_type="pickle"):
        self.data[file_name] = data

    def load(self, file_name, data_type="pickle"):
        return self.data[file_name]

    @property
    def file_not_found_exception(self):
        return ValueError


class testStorageBackendConfig(unittest.TestCase):
    def testLoadLocalStorageConfigValid(self):
        from chainsail.common.storage import StorageBackendConfigSchema

        StorageBackendConfigSchema().load(LOCAL_STORAGE_CONFIG)

    def testLoadCloudStorageConfigValid(self):
        from chainsail.common.storage import StorageBackendConfigSchema

        StorageBackendConfigSchema().load(CLOUD_STORAGE_CONFIG)


class testFunctions(unittest.TestCase):
    def testPickleToStream(self):
        res = load(pickle_to_stream(obj))
        expected = obj
        self.assertEqual(res, expected)


class testSimulationStorage(unittest.TestCase):
    def setUp(self):
        mock_config = {
            "general": {"num_replicas": 2, "n_iterations": 10},
            "re": {"dump_interval": 5},
        }
        patcher = patch(
            "chainsail.common.storage.SimulationStorage.load_config",
            return_value=mock_config,
        )
        patcher.start()
        self.addCleanup(patcher, patcher.stop)

        self._basename = "/some/base"
        self._sim_path = "/sim/path"
        self._backend = MockStorageBackend()
        self._storage = SimulationStorage(self._basename, self._sim_path, self._backend)

    def testWrite(self):
        fname = "a_file.pickle"
        self._storage.save(obj, fname)
        full_fname = os.path.join(self._basename, self._sim_path, fname)
        self.assertTrue(full_fname in self._backend.data)
        self.assertEqual(self._backend.data[full_fname], obj)

        fname = "folder/a_file.pickle"
        self._storage.save(obj, fname)
        full_fname = os.path.join(self._basename, self._sim_path, fname)
        self.assertTrue(full_fname in self._backend.data)
        self.assertEqual(self._backend.data[full_fname], obj)

    def testLoad(self):
        fname = "a_file.pickle"
        full_fname = os.path.join(self._basename, self._sim_path, fname)
        self._backend.data[full_fname] = obj
        self.assertEqual(self._storage.load(fname), obj)

        fname = "folder/a_file.pickle"
        full_fname = os.path.join(self._basename, self._sim_path, fname)
        self._backend.data[full_fname] = obj
        self.assertEqual(self._storage.load(fname), obj)

    def _write_fake_all_quantities(self, what, jagged=False):
        template = os.path.join(self._basename, self._sim_path, f"{what}/{what}")
        template += "_replica{}_{}-{}.pickle"
        self._backend.data[template.format(1, 0, 5)] = [1, 2, 3]
        self._backend.data[template.format(1, 5, 10)] = [4, 5, 6]
        self._backend.data[template.format(2, 0, 5)] = [7, 8, 9]
        if not jagged:
            self._backend.data[template.format(2, 5, 10)] = [10, 11, 12]
        else:
            self._backend.data[template.format(2, 5, 10)] = [10, 11]

    def testLoadAllEnergies(self):
        self._write_fake_all_quantities("energies")
        energies = self._storage.load_all_energies()
        expected = np.array([[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]])
        self.assertTrue(np.all(energies == expected))

        energies = self._storage.load_all_energies(from_sample=5)
        expected = np.array([[4, 5, 6], [10, 11, 12]])
        self.assertTrue(np.all(energies == expected))

        energies = self._storage.load_all_energies(from_sample=5, step=2)
        expected = np.array([[4, 6], [10, 12]])
        self.assertTrue(np.all(energies == expected))

    def testLoadAllEnergies_jagged(self):
        self._write_fake_all_quantities("energies", jagged=True)
        energies = self._storage.load_all_energies()
        expected = np.array([[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11]], dtype=object)
        self.assertTrue(np.all([np.all(ref == out) for ref, out in zip(expected, energies)]))

        energies = self._storage.load_all_energies(from_sample=5)
        expected = np.array([[4, 5, 6], [10, 11]], dtype=object)
        self.assertTrue(np.all([np.all(ref == out) for ref, out in zip(expected, energies)]))

        energies = self._storage.load_all_energies(from_sample=5, step=2)
        expected = np.array([[4, 6], [10]], dtype=object)
        self.assertTrue(np.all([np.all(ref == out) for ref, out in zip(expected, energies)]))

    def testLoadAllSamples(self):
        self._write_fake_all_quantities("samples")
        samples = self._storage.load_all_samples()
        expected = np.array([[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]])
        self.assertTrue(np.all(samples == expected))

        samples = self._storage.load_all_samples(from_sample=5)
        expected = np.array([[4, 5, 6], [10, 11, 12]])
        self.assertTrue(np.all(samples == expected))

        samples = self._storage.load_all_samples(from_sample=5, step=2)
        expected = np.array([[4, 6], [10, 12]])
        self.assertTrue(np.all(samples == expected))


class TestLocalStorage(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = TemporaryDirectory().name
        self._backend = LocalStorageBackend()

    def testWrite(self):
        s = "I'm a string"
        fname = "somedir/string.txt"
        full_path = os.path.join(self._tmp_dir, fname)
        self._backend.write(s, full_path, data_type="text")
        self.assertTrue(os.path.exists(full_path))
        with open(full_path) as f:
            self.assertEqual(s, f.read())

        o = ["I live in a list"]
        fname = "somedir/list.pickle"
        full_path = os.path.join(self._tmp_dir, fname)
        self._backend.write(o, full_path, data_type="pickle")
        self.assertTrue(os.path.exists(full_path))
        with open(full_path, "rb") as f:
            self.assertEqual(o, load(f))

        with self.assertRaises(ValueError):
            self._backend.write("moo", "a/path", "invalid_data_type")

    def testRead(self):
        s = "I'm a string"
        fname = "somedir/string.txt"
        full_path = os.path.join(self._tmp_dir, fname)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(s)
        self.assertEqual(self._backend.load(full_path, "text"), s)

        o = ["I live in a list"]
        fname = "somedir/list.pickle"
        full_path = os.path.join(self._tmp_dir, fname)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            dump(o, f)
        self.assertEqual(self._backend.load(full_path, "pickle"), o)

        with self.assertRaises(ValueError):
            self._backend.load("a/path", "invalid_data_type")
