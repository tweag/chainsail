# re_job_controller

Controller application for running sampling jobs.  Invoking the controller
will execute the sampling job, exposing a gRPC endpoint for job monitoring (this is still a WIP).

# Sampling runners

This application can use any implementation of [AbstractRERunner](). By default, it comes with the
the rexfw + MPI runner defined in [../runners/rexfw](../runners/rexfw) installed. 
