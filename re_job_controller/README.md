# re_job_controller

Controller application for running sampling jobs.  Invoking the controller
will execute the sampling job, exposing a gRPC endpoint for job monitoring (this is still a WIP).

# Sampling runners

This application can use any implementation of [AbstractRERunner](). The runner class is specified 
in the controller configuration file and is loaded *at runtime*. The controller comes packaged with
builtin runners as package extras and they must be installed explicitly. 

Available runners:

* `rexfw` -> `poetry install --extras rexfw`

# Configuration

See the example file in [../scheduler/example/controller.yaml](../scheduler/example/controller.yaml)
