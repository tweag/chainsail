# Running the job controller + MPI runner locally
This provides config files to run the full job controller main loop (optimization runs, schedule optimization and a production run) independent from the rest of RESAAS and without the need to set up a Docker Compose cluster.

## Instructions
Make sure you are within the Nix shell provided in the directory root.
```bash
$ cd ../../controller
$ poetry install --extras rexfw
$ poetry run resaas-controller-local \
  --basename /tmp/test_simulation \
  --job-spec ../examples/local_run/job.json
```
