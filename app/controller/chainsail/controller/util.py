"""
Shared code
"""


def schedule_length(schedule):
    return len(list(schedule.values())[0])


# TODO: just parking this here
def _check_compatibility(self, initial_schedule_params, optimization_params):
    """
    Check whether initial schedule parameters are compatible with the
    optimization parameters.

    Args:
        initial_schedule_params(dict): initial schedule parameters
        optimization_params(dict): optimization params
    """
    # TODO: check whether optimization params and initial schedule params
    # are compatible. Although that's a late failure - perhaps do this upon
    # job submission?
    pass
