import numpy as np
import matplotlib.pyplot as plt

from sampler import RWMCSampler

from probability import pdf

initial_state = np.random.uniform(-5, 5, size=(2, 2))

if False:
    from scipy.optimize import fmin
    optimal_params = fmin(
        lambda x: -pdf.log_prob(x.reshape(-1, 2)),
        initial_state.ravel())
    initial_state = optimal_params.reshape(-1, 2)

sampler = RWMCSampler(pdf, initial_state, stepsize=0.1)

if not False:
    samples = []
    accepted = 0
    n_samples = 50000
    for i in range(n_samples):
        samples.append(sampler.sample())
        accepted += sampler._last_move_accepted

        if i % 500 == 0 and i > 1:
            print("Samples: {}/{} ### acceptance rate: {:.2f}".format(
                i, n_samples, accepted / i))

    log_probs = np.array([pdf.log_prob(x) for x in samples])
    optimal_params = samples[np.argmin(log_probs)]

if False:
    from scipy.optimize import fmin
    optimal_params = fmin(
        lambda x: -pdf.log_prob(x.reshape(-1,2)),
        initial_state.ravel())
    optimal_params = optimal_params.reshape(-1, 2)

fig, ax = plt.subplots()
xspace = np.linspace(-10, 10)
ax.scatter(pdf.data_x, pdf.data_y)
for (a, b) in optimal_params:
    ax.plot(xspace, a * xspace + b, c="blue")
plt.show()
