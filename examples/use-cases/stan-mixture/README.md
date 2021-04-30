# Gaussian mixture in Stan

This demonstrates how to use a Stan model with RESAAS. Sampling is quite slow because of repeated calls to the `httpstan` API for log-probability and gradient evaluations.

TODO: the `PDF` class should be in some more general place.
