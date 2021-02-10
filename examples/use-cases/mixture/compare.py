import sys
import numpy as np
import matplotlib.pyplot as plt

from plots import plot_true_distribution, plot_samples_histogram


ensemble = int(sys.argv[1])

sc_samples = np.load('sc_samples.npy')
re_samples = np.load('re_all_samples.npy')

fig, (ax1, ax2, ax3) = plt.subplots(1, 3)
plot_true_distribution(ax1)
plot_samples_histogram(ax2, sc_samples, 'single chain')
plot_samples_histogram(ax3, re_samples[ensemble], 'RE via RESAAS')
plt.show()
