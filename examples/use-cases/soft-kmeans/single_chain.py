import numpy as np

import matplotlib.pyplot as plt

from rexfw.samplers.rwmc import RWMCSampler

from probability import pdf, initial_state
from plots import plot_data_samples

sampler = RWMCSampler(pdf, initial_state, 0.02)
n = pdf.num_clusters


samples = []
accepted = 0
n_samples = 10000
for i in range(n_samples):
    samples.append(sampler.sample().reshape(-1, 2))
    accepted += sampler._last_move_accepted

    if i % 500 == 0 and i > 1:
        print("Samples: {}/{} ### acceptance rate: {:.2f}".format(
            i, n_samples, accepted / i))
        print(sampler.timestep)
samples = np.array(samples)

fig, ax = plt.subplots()
plot_data_samples(ax, samples)

np.save("sc_samples.npy", samples)
