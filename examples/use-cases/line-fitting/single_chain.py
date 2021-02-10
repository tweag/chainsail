import matplotlib.pyplot as plt
import numpy as np

from rexfw.samplers.rwmc import RWMCSampler

from probability import pdf, initial_state
from plots import plot_data_samples

sampler = RWMCSampler(pdf, initial_state, stepsize=0.1)

samples = []
accepted = 0
n_samples = 10000
for i in range(n_samples):
    samples.append(sampler.sample())
    accepted += sampler._last_move_accepted

    if i % 500 == 0 and i > 1:
        print("Samples: {}/{} ### acceptance rate: {:.2f}".format(
            i, n_samples, accepted / i))
samples = np.array(samples)

fig, ax = plt.subplots()
plot_data_samples(ax, samples[::100], "single chain")
plt.show()

np.save('sc_samples.npy', samples)
