import numpy as np
import requests


class PDF:
    STAN_SERVER_ADDRESS = "http://localhost"

    def __init__(self, model_code, data, port=8082):
        self._port = port
        try:
            r = requests.post(
                f"{self.STAN_SERVER_ADDRESS}:{self._port}/v1/models",
                json={"program_code": model_code}
            )
            r.raise_for_status()
            self._model_id = r.json()['name']
        except Exception as e:
            raise Exception(f"Model compilation failed. Error: {e}")
        self._data = data

    def log_prob(self, x):
        try:
            r = requests.post(
                f"{self.STAN_SERVER_ADDRESS}:{self._port}/v1/{self._model_id}/log_prob",
                json={"unconstrained_parameters": x.tolist(),
                      "data": self._data,
                      "adjust_transform": False}
            )
            r.raise_for_status()
            return r.json()["log_prob"]
        except Exception as e:
            raise Exception(f"Querying log-prob failed: Error: {e}")

    def log_prob_gradient(self, x):
        try:
            r = requests.post(
                f"{self.STAN_SERVER_ADDRESS}:{self._port}/v1/{self._model_id}/log_prob_grad",
                json={"unconstrained_parameters": x.tolist(),
                      "data": self._data,
                      "adjust_transform": False}
            )
            r.raise_for_status()
            return np.array(r.json()["log_prob_grad"])
        except Exception as e:
            raise Exception(f"Querying log-prob gradient failed: Error: {e}")


model_code = """
data {
  int<lower=0> N;  // number of data points
  int<lower=1> D;  // number of dimensions
  int<lower=1> K;  // number of clusters
  vector[D] y[N];  // observations
}
transformed data {
  real<upper=0> neg_log_K;
  neg_log_K = -log(K);
}
parameters {
  vector[D] mu[K]; // cluster means
}
transformed parameters {
  real<upper=0> soft_z[N, K]; // log unnormalized clusters
  for (n in 1:N)
    for (k in 1:K)
      soft_z[n, k] = neg_log_K
                     - 0.5 * dot_self(mu[k] - y[n]);
}
model {
  // prior
  for (k in 1:K)
    mu[k] ~ std_normal();

  // likelihood
  for (n in 1:N)
    target += log_sum_exp(soft_z[n]);
}"""

# make data
spacing = 1
sigma = 0.25
sl = 3

cov = np.eye(2) * sigma * sigma

data_points = []
for mean_x in np.arange(0, spacing * sl, spacing):
    for mean_y in np.arange(0, spacing * sl, spacing):
        data_points.append(
            np.random.multivariate_normal((mean_x, mean_y), cov, size=25))
data_points = np.vstack(data_points)

# compile stan model
data = {"N": len(data_points), "D": 2, "K": 9, "y": data_points.tolist()}

pdf = PDF(model_code, data)
initial_states = np.random.uniform(0, 3, data["D"] * data["K"])
