import matplotlib
import numpy as np

from probability import pdf

minn = -4
maxx = 4
sl = 100


def plot_true_distribution(ax):
    grid = np.zeros((sl, sl))
    for i, x in enumerate(np.linspace(minn, maxx, sl)):
        for j, y in enumerate(np.linspace(minn, maxx, sl)):
            grid[i, j] = np.exp(pdf.log_prob(np.array([x, y])))
    ax.imshow(grid.T, origin="lower")
    ax.set_title("true distribution")


def plot_samples_histogram(ax, samples, title=""):
    ax.hist2d(
        *samples.T,
        bins=np.linspace(minn, maxx, sl),
        density=True,
        norm=matplotlib.colors.LogNorm(),
    )
    ax.set_aspect("equal")
    ax.set_title("single chain")
    ax.set_title(title)
