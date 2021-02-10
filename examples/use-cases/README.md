# Example RESAAS use cases
This provides several use cases for RESAAS, in which a single Markov chain fails to accurately sample a multimodal distribution. 
To load the results of a RESAAS simulation, enter a `poetry shell` and run the `resaas_results.py` script as follows:
```bash
$ python resaas_results.py /tmp/my/simulation/path production_run mixture
```
to load the RESAAS results which have been written to `/tmp/my/simulation/path/production_run` and write a NumPy "pickle" of all samples to the `mixture` directory (replace with other use case directories as needed). Then you can use the `compare.py` script within the use case folder to compare the RESAAS results to a single chain run, which you must have performed before by running `python single_chain.py` in a use case folder before.
