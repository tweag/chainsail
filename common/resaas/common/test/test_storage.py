import os
import unittest
from pickle import load, dump
from tempfile import TemporaryDirectory


from resaas.common.storage import (
    SimulationStorage,
    pickle_to_stream,
    LocalStorageBackend)


obj = ["a", "list", 42]


class MockStorageBackend:
    def __init__(self):
        self.data = {}

    def write(self, data, file_name, data_type="pickle"):
        self.data[file_name] = data

    def load(self, file_name, data_type="pickle"):
        return self.data[file_name]


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
