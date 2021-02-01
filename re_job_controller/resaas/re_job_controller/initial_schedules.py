'''
Classes for making initial schedules
'''

import numpy as np


def make_geometric_schedule(param_name, num_replicas, min_value,
                            max_value=1.0):
    '''
    Schedule maker which makes a schedule using a geometric progression.

    In fact it creates a geometric progression in the temperatures,
    but which are then converted into _inverse_ temperatures.

    Args:
        param_name(str): name of replica parameter
        min_value(float): minimum parameter value
        max_value(float): maximum parameter value
        num_replicas(int): number of replicas
    '''
    max_temp = 1 / min_value
    min_temp = 1 / max_value
    common_ratio = (max_temp / min_temp) ** (1 / (num_replicas - 1))
    geometric_progression = min_temp * common_ratio ** np.arange(num_replicas)

    return {param_name: 1 / geometric_progression}
