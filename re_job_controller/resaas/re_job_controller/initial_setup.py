'''
Logic to set up initial states and values for Replica Exchange simulations
'''
import numpy as np

from resaas.common.util import log_sum_exp
from resaas.re_job_controller.util import schedule_length


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
    this linearly interpolates new timesteps for the new schedule.
    Works only for single, monotonously decreasing schedule parameters!

    Args:
        schedule(dict): current parameter schedule
        old_schedule(dict): previous parameter schedule
        old_timesteps(dict): previous set of time steps
    '''
    if len(schedule) > 1 or len(old_schedule) > 1:
        raise ValueError(("Time steps can be interpolated only for "
                          "single-parameter schedules"))
    new_params = list(schedule.values())[0]
    old_params = list(old_schedule.values())[0]

    err_msg = "{} schedule parameters must be a decreasing sequence"
    if not np.all(np.diff(new_params) < 0):
        raise ValueError(err_msg.format("New"))
    if not np.all(np.diff(old_params) < 0):
        raise ValueError(err_msg.format("Old"))
    if len(old_params) != len(old_timesteps):
        raise ValueError(
            "Old schedule parameters and old timesteps must have same length")

    # np.interp() expects the sequence of x values to increase, but
    # our schedules always have the highest inverse temperature first,
    # so we have to reverse everything and later reverse the result back
    interpolated_timesteps = np.interp(
        new_params[::-1], old_params[::-1], old_timesteps[::-1])

    return interpolated_timesteps[::-1]


def draw_initial_states(schedule, previous_storage, dos, dos_burnin,
                        dos_thinning_step):
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
        dos_burnin(int): number of burnin samples used when density of
          states was calculated
        dos_thinning_step(int): sample thinning step used when density of
          states was calculated
    '''
    betas = schedule['beta']
    energies = previous_storage.load_all_energies(from_sample=dos_burnin,
                                                  step=dos_thinning_step)
    energies = energies.ravel()

    # calculate the probability weights of the old samples for the new
    # inverse temperatures.
    # TODO: the shape-shifting is a bit annoying; we might want to improve
    # the log_sum_exp function to avoid this
    # TODO: write a PDF where this is explained and link to it in the doc
    # string
    log_ps = -energies * betas[:, None] + dos[None, :]
    # the above are the unnormalized weights, now we normalize them
    log_ps -= log_sum_exp(log_ps.T, axis=0).T[:, None]

    old_samples = previous_storage.load_all_samples(from_sample=dos_burnin,
                                                    step=dos_thinning_step)
    # choose new samples from categorical distribution over old samples
    # with the above calculated weights
    ensemble_flattened_samples = old_samples.reshape(-1, *old_samples.shape[2:])

    rng = np.random.default_rng()
    new_samples = np.array([
        rng.choice(ensemble_flattened_samples, axis=0, p=np.exp(log_p))
        for log_p, beta in zip(log_ps, betas)])

    return new_samples


def setup_initial_states(current_storage, schedule, previous_storage,
                         dos_from_samples, dos_thinning_step):
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
        dos_from_sample(int): number of burnin samples used when density of
          states was calculated
        dos_thinning_step(int): sample thinning step used when density of
          states was calculated
    '''
    if previous_storage is not None:
        dos = previous_storage.load_dos()
        initial_states = draw_initial_states(
            schedule, previous_storage, dos, dos_from_samples,
            dos_thinning_step)
        current_storage.save_initial_states(initial_states)
