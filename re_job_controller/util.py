import numpy as np

def log_sum_exp(x, axis=0):
    '''
    Calculate the log of a sum of exponentials in a numerically
    stable way
    '''
    xmax = x.max(axis)
    return np.log(np.exp(x - xmax).sum(axis)) + xmax
