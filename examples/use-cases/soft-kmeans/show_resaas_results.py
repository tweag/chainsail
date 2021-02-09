import matplotlib.pyplot as plt
import numpy as np

from probability import pdf

samples = np.load('re_all_samples.npy')

print(samples.shape)

colors = ("green", "red", "blue", "black", "yellow", "gray", "orange", "lightblue", "cyan")
fig, ax = plt.subplots()
ax.scatter(*pdf.data.T, label="data")
print("ping")
for s in samples[::100]:
    s = s.reshape(-1, 2)
    for i, c in enumerate(s):
        ax.scatter((c[0],), (c[1],), color=colors[i], s=75, marker='x', alpha=0.5)
ax.legend()
plt.show()
