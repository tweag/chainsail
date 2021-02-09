import sys

import numpy as np

spacing = 3.0
sigma = 0.75
sl = 3
n_dim = 2

cov = np.eye(n_dim) * sigma * sigma
n_data = 200
data_points = []
for mean_x in np.arange(0, spacing * sl, spacing):
    for mean_y in np.arange(0, spacing * sl, spacing):
        mean_x += np.random.uniform(-0.5, 0.5)
        mean_y += np.random.uniform(-0.5, 0.5)
        data_points.append(
            np.random.multivariate_normal((mean_x, mean_y), cov, size=np.random.choice(np.arange(n_data - 20, n_data + 20))))
data_points = np.vstack(data_points)
print(data_points.shape)

import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.scatter(*data_points.T, alpha=0.5)
plt.show()

np.savetxt(sys.argv[1], data_points.T)
