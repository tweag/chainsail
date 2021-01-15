import numpy as np

from dos_calculators import BoltzmannDOSCalculator
from schedule_optimizers import BoltzmannAcceptanceRateOptimizer

# draw samples from a bunch of normal distributions with standard deviations
# 1, 2, ...
sigmas = np.arange(1, 5)
samples = np.array([np.random.normal(0, s, size=200) for s in sigmas])
# calculate the "energies"
energies = 0.5 * samples ** 2
# morph normal distributions into samples of harmonic oscillator at different
# inverse temperatures beta = 1 / sigma ** 2
schedule = {'beta': 1.0 / sigmas ** 2}

dc = BoltzmannDOSCalculator(max_wham_iterations=20)
log_dos = dc.calculate_dos(energies, schedule)

optimizer = BoltzmannAcceptanceRateOptimizer(log_dos, energies)
# find schedule s.t. acceptance rates are always 80% and with a minimum beta
# of 0.01
optimized_schedule = optimizer.optimize(0.8, 1.0, 0.01, 1e-2)
print('Optimized schedule: ', ['{:.3f}'.format(x) for x in optimized_schedule['beta']])
