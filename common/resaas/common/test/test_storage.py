import os
import unittest
from pickle import load

from resaas.common.storage import SimulationStorage, pickle_to_stream

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


class testStorageBackendConfig(unittest.TestCase):
    def testLoadLocalStorageConfigValid(self):
        from resaas.common.storage import StorageBackendConfigSchema

        StorageBackendConfigSchema().load(LOCAL_STORAGE_CONFIG)

    def testLoadCloudStorageConfigValid(self):
        from resaas.common.storage import StorageBackendConfigSchema

        StorageBackendConfigSchema().load(CLOUD_STORAGE_CONFIG)


class testFunctions(unittest.TestCase):
    def testPickleToStream(self):
        res = load(pickle_to_stream(obj))
        expected = obj
        self.assertEqual(res, expected)


class testSimulationStorage(unittest.TestCase):
    def setUp(self):
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
