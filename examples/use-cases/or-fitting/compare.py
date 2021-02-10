import sys

import matplotlib.pyplot as plt
import numpy as np

from plots import plot_data_samples
from probability import pdf

ensemble = int(sys.argv[1])

sc_samples = np.load("sc_samples.npy")
print("SC samples shape:", sc_samples.shape)
re_all_samples = np.load("re_all_samples.npy")
print("RE samples shape:", re_all_samples.shape)

fig, (ax1, ax2) = plt.subplots(1, 2)
mean_lp_sc = np.mean([pdf.log_prob(x) for x in sc_samples])
step_factor = 10
plot_data_samples(
    ax1, sc_samples[::5 * step_factor], "single chain\nlog-prob: {:.2f}".format(mean_lp_sc))
mean_lp_re = np.mean([pdf.log_prob(x) for x in re_all_samples[ensemble]])
plot_data_samples(
    ax2, re_all_samples[ensemble,::step_factor],
    "RE via RESAAS\nlog-prob: {:.2f}".format(mean_lp_re))
fig.tight_layout()
plt.show()
