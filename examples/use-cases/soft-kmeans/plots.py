import numpy as np

data = np.load("data.txt").T


def plot_data(ax, alpha=1.0):
    ax.scatter(*data.T, label="data", alpha=alpha)


def plot_data_samples(ax, samples, title):
    colors = ("green", "red", "blue", "black", "yellow", "gray", "orange",
              "lightblue", "cyan")
    plot_data(ax, 0.5)
    for s in samples[::100]:
        s = s.reshape(-1, 2)
        for i, c in enumerate(s):
            ax.scatter((c[0],), (c[1],), color=colors[i], s=75, marker='x',
                       alpha=0.5)
    ax.set_title(title)
