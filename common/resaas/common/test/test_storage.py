import os
import unittest
from pickle import load
from tempfile import mkdtemp

from resaas.common.storage import (FileSystemPickleStorage,
                                   sanitize_basename,
                                   pickle_to_stream)


class testFunctions(unittest.TestCase):
    def testSanitizeBasename(self):
        res1 = sanitize_basename('/this/is/a/path')
        expected1 = '/this/is/a/path/'
        self.assertEqual(res1, expected1)

        res2 = sanitize_basename('/this/is/a/path/')
        expected2 = '/this/is/a/path/'
        self.assertEqual(res2, expected2)

    def testPickleToStream(self):
        obj = ['a', 'list', 42]
        res = load(pickle_to_stream(obj))
        expected = obj
        self.assertEqual(res, expected)


class testFileSystemPickleStorage(unittest.TestCase):
    def setUp(self):
        self._tmpdir = mkdtemp()
        self._writer = FileSystemPickleStorage(self._tmpdir)

    def testWrite(self):
        obj = ['a', 'list', 42]

        self._writer.write(obj, 'a_file.pickle')
        with open(self._tmpdir + '/a_file.pickle', 'rb') as ipf:
            res1 = load(ipf)
            self.assertEqual(obj, res1)

        different_basename = self._tmpdir + '/some_dir'
        os.makedirs(different_basename, exist_ok=True)
        self._writer.write(obj, 'another_file.pickle', different_basename)
        with open(different_basename + '/another_file.pickle', 'rb') as ipf:
            res2 = load(ipf)
            self.assertEqual(obj, res2)

        different_basename_wslash = self._tmpdir + '/some_dir/'
        os.makedirs(different_basename_wslash, exist_ok=True)
        self._writer.write(obj, 'another_file.pickle', different_basename_wslash)
        file_path = different_basename_wslash[:-1] + '/another_file.pickle'
        with open(file_path, 'rb') as ipf:
            res3 = load(ipf)
            self.assertEqual(obj, res3)
