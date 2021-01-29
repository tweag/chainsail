'''
Classes for making initial schedules
'''

import numpy as np


def make_geometric_schedule(param_name, num_replicas, min_value,
                            max_value=1.0):
    '''
    Schedule maker which makes a schedule using a geometric progression.

    Args:
        param_name(str): name of replica parameter
        min_value(float): minimum parameter value
        max_value(float): maximum parameter value
        num_replicas(int): number of replicas
    '''
    common_ratio = (max_value / min_value) ** (1. / num_replicas)
    geometric_progression = common_ratio ** np.arange(num_replicas)

    return {param_name: geometric_progression}
