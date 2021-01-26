import numpy as np

from .storage import LocalStorageBackend, CloudStorageBackend

def log_sum_exp(x, axis=0):
    """Calculate the log of a sum of exponentials in a numerically
    stable way

    Args:
      x: 
      axis:  (Default value = 0)

    Returns:

    """
    xmax = x.max(axis)
    return np.log(np.exp(x - xmax).sum(axis)) + xmax


def storage_factory():
    """Creates storage objects, which, depending on the environment, either
    access a local file system or a cloud storage.

    Args:
      path(str): base path of a simulation

    Returns:

    """
    # TODO: make environment-dependent
    return LocalStorageBackend()
