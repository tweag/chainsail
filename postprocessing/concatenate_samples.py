"""
Hacky script to concatenate target replica samples
"""
import glob
import os
import sys

import numpy as np


simulation_run = sys.argv[1]
output_file = sys.argv[2]

with open(os.path.join(simulation_run, "config.yml")) as f:
    dump_interval = None
    for l in f.readlines():
        if l.lstrip().startswith("dump_interval"):
            dump_interval = int(l.split(":")[1].strip())

ctr = 0
samples = []
while True:
    try:
        fname = "samples_replica1_{}-{}.pickle".format(ctr, ctr + dump_interval)
        samples += np.load(os.path.join(simulation_run, "samples", fname), allow_pickle=True)
        ctr += dump_interval
    except FileNotFoundError:
        break

np.save(output_file, np.array(samples))
