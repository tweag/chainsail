'''
This is just FYI and will not be run during tests.
It calculates the exact acceptance rate for two normal distributions
at different precisions by direct numerical integration.
'''
import sys
import numpy as np
from scipy.integrate import dblquad

def pacc(x, y, beta1, beta2):
    integrand = min(np.exp(-0.5 * x ** 2 * beta1 - 0.5 * y ** 2 * beta2),
                    np.exp(-0.5 * y ** 2 * beta1 - 0.5 * x ** 2 * beta2))
    return integrand / (np.sqrt(2 * np.pi / beta1) * np.sqrt(2 * np.pi / beta2))

beta1 = float(sys.argv[1])
beta2 = float(sys.argv[2])
pakk = lambda x, y: pacc(x, y, beta1, beta2)
print(dblquad(pakk, -np.inf, np.inf, lambda x: -np.inf, lambda x: np.inf)[0])
