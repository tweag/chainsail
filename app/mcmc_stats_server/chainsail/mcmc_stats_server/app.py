from io import BytesIO, StringIO
from itertools import chain
import os
from pickle import load

from flask import Flask, jsonify
from google.cloud import storage
import numpy as np
import yaml

from chainsail.common.storage import load_storage_backend, SimulationStorage

app = Flask(__name__)

storage_config = yaml.safe_load(open(os.getenv("STORAGE_CONFIG")))

storage_backend = load_storage_backend("cloud", storage_config["backend_config"]["cloud"])
basename = os.getenv("STORAGE_BASENAME")
if not basename:
    raise ValueError("STORAGE_BASENAME not set")


@app.route("/mcmc_stats/<job_id>/<simulation_run>/neg_log_prob_sum", methods=["GET"])
def neg_log_prob_sum(job_id, simulation_run):
    storage = SimulationStorage(basename, f"{job_id}/{simulation_run}", storage_backend)
    energies = storage.load_all_energies(fail_if_not_existing=False)
    dump_step = storage.load_config()["re"]["dump_step"]
    try:
        summed_energies = energies.sum(0)
    except ValueError:
        # this is raised if the array is jagged, i.e., not all energies have been written
        # out yet for a given sampling step
        min_n_energies = min(map(len, energies))
        energies = np.array([single_replica_energies[:min_n_energies]
                             for single_replica_energies in energies])
        summed_energies = energies.sum(0)
    return jsonify(
        {i * dump_step: summed_energy for i, summed_energy in enumerate(summed_energies)}
    )


@app.route("/mcmc_stats/<job_id>/<simulation_run>/re_acceptance_rates", methods=["GET"])
def re_acceptance_rates(job_id, simulation_run):
    client = storage.Client()
    bucket = client.bucket(storage_config["backend_config"]["cloud"]["container_name"])
    config_blob = bucket.blob(f"{basename}/{job_id}/{simulation_run}/statistics/re_stats.txt")
    stats = np.loadtxt(StringIO(config_blob.download_as_text()), dtype=float)
    return jsonify({int(step_data[0]): list(step_data[1:]) for step_data in stats})
