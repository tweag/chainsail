import numpy as np

from .storage import (FileSystemPickleStorage,
                      FileSystemStringStorage)

def log_sum_exp(x, axis=0):
    '''
    Calculate the log of a sum of exponentials in a numerically
    stable way
    '''
    xmax = x.max(axis)
    return np.log(np.exp(x - xmax).sum(axis)) + xmax


def storage_factory(path):
    '''
    Creates storage objects, which, depending on the environment, either
    access a local file system or a cloud storage.

    :param path: base path of a simulation
    :type path: str
    '''
    pstorage = FileSystemPickleStorage(path)
    sstorage = FileSystemStringStorage(path)
    return pstorage, sstorage
