'''
Logic to set up initial states and values for Replica Exchange simulations
'''
import numpy as np

from resaas.common.util import log_sum_exp
from .util import schedule_length


def setup_timesteps(current_storage, schedule, previous_storage=None):
    '''
    Sets up time steps, possibly based on a previous simulation.

    Args:
        current_storage(:class:`SimulationStorage`): storage for simulation
          to be set up
        schedule(dict): current parameter schedule
        previous_storage(:class:`SimulationStorage`): storage for previous
          simulation
    '''
    if previous_storage is None:
        timesteps = np.linspace(1e-3, 1e-1, len(schedule))
    else:
        old_timesteps = previous_storage.load_final_timesteps()
        old_schedule = previous_storage.load_schedule()
        timesteps = interpolate_timesteps(schedule, old_schedule,
                                          old_timesteps)
    current_storage.save_initial_timesteps(timesteps)


def interpolate_timesteps(schedule, old_schedule, old_timesteps):
    '''
    Interpolates time steps from a previous simulation.

    Given time steps from a previous simulation and its schedule,
    this interpolates between these time steps to a new schedule
    length.

    Args:
        schedule(dict): current parameter schedule
        old_schedule(dict): previous parameter schedule
        old_timesteps(dict): previous set of time steps
    '''
    # TODO: somehow interpolate timesteps from old simulation, e.g., by
    # fitting spline or just simple linear interpolation
    return np.array([0.001] * schedule_length(schedule))


def draw_initial_states(schedule, previous_storage, dos):
    '''
    Draw initial states using the density of states.

    Given previous samples, their energies, and the current parameter
    schedule, this uses the density of states to calculate probability
    weights of the previous samples under the new schedule and uses
    those weights to sample fitting new initial states from the existing
    samples.
    TODO: this currently loads all states in memory. We should be able to,
    via the Replica Exchange dump_interval parameter, load selectively only
    the states whose energies are drawn in the end.

    Args:
        schedule(dict): current temperature schedule
        previous_storage(:class:`SimulationStorage`): storage allowing to
          access the previous simulation's results
        dos(:class:`np.array`): density of states estimate of previous
          simulation
    '''
    betas = schedule['beta']
    energies = previous_storage.load_all_energies().ravel()

    # calculate the probability weights of the old samples for the new
    # inverse temperatures.
    # TODO: the shape-shifting is a bit annoying; we might want to improve
    # the log_sum_exp function to avoid this
    # TODO: write a PDF where this is explained and link to it in the doc
    # string
    log_ps = -energies * betas[:, None] + dos[None, :]
    # the above are the unnormalized weights, now we normalize them
    log_ps -= log_sum_exp(log_ps.T, axis=0).T[:, None]

    old_samples = previous_storage.load_all_samples()
    # choose new samples from categorical distribution over old samples
    # with the above calculated weights
    new_samples = np.array([
        np.random.choice(old_samples.ravel(), p=np.exp(log_p))
        for log_p, beta in zip(log_ps, betas)])

    return new_samples


def setup_initial_states(current_storage, schedule, previous_storage=None):
    '''
    Sets up initial states.

    Uses the density of states to draw new initial states and writes them
    to the simulation directory.

    Args:
        current_storage(:class:`SimulationStorage`): storage for simulation
          to be set up
        schedule(dict): current paramter schedule
        previous_storage(:class:`SimulationStorage`): storage for previous
          simulation
    '''
    if previous_storage is not None:
        dos = previous_storage.load_dos()
        initial_states = draw_initial_states(
            schedule, previous_storage, dos)
        current_storage.save_initial_states(initial_states)
