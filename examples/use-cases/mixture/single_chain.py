import numpy as np
import matplotlib.pyplot as plt

from rexfw.samplers.rwmc import RWMCSampler

from probability import pdf, initial_state
from plots import plot_true_distribution, plot_samples_histogram

sampler = RWMCSampler(pdf, initial_state, 0.5)

samples = []
accepted = 0
n_samples = 10000
for i in range(n_samples):
    samples.append(sampler.sample())
    accepted += sampler._last_move_accepted

    if i % 500 == 0 and i > 1:
        print("Samples: {}/{} ### acceptance rate: {:.2f}".format(i, n_samples, accepted / i))

fig, (ax1, ax2) = plt.subplots(1, 2)
plot_true_distribution(ax1)
plot_samples_histogram(ax2, np.array(samples), "single chain")
fig.tight_layout()
plt.show()

np.save("sc_samples.npy", np.array(samples))
