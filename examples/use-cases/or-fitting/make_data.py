import sys

import matplotlib.pyplot as plt

import numpy as np

a = 0.5
b = 0
xs_line = np.linspace(-5, 5, 30)
ys1_line = np.random.normal(a * xs_line + b)
ys2_line = np.random.normal(-a * xs_line + b)

np.savetxt(sys.argv[1], np.vstack((xs_line, ys1_line, ys2_line)).T)

from plots import plot_data

fig, ax = plt.subplots()
plot_data(ax)
plt.show()
