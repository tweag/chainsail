import numpy as np

from resaas.controller.initial_schedules import make_geometric_schedule


def test_geometric_schedule():
    min_temp = 1.0
    max_temp = 10000
    n_temps = 5
    result = make_geometric_schedule("beta", n_temps, 1 / max_temp, 1 / min_temp)
    expected = {"beta": 0.1 ** np.arange(n_temps)}
    assert np.allclose(result["beta"], expected["beta"])
