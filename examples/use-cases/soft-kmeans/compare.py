import sys
import numpy as np
import matplotlib.pyplot as plt

from plots import plot_data_samples

ensemble = int(sys.argv[1])

sc_samples = np.load('sc_samples.npy')
re_samples = np.load('re_all_samples.npy')

fig, (ax1, ax2) = plt.subplots(1, 2)
plot_data_samples(ax1, sc_samples, 'single chain')
plot_data_samples(ax2, re_samples[ensemble], 'RE via RESAAS')
plt.show()
