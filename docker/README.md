# docker

Docker images for all chainsail back-end components.

## Building

Build using the make:

```console
cd ..

make images
```

## Descriptions
### scheduler

Scheduler app behind a uWSGI app server and an NGINX reverse proxy.

### celery

The celery worker for the scheduler.

### mcmc-stats-server

A small server which queries chainsail job storage and returns MCMC samples.

### user-code

A small gRPC server which evaluates user-defined probability distributions.

### httpstan-server

An http-stan server which can be used for evalulating Stan models.

### node

Docker image containing all dependencies required to run resaas job nodes, including
`controller`.

Accepts the following configurations:

  1. **ssh**
     1. SSH public keys can be specified by mounting an authorized_keys file to `/app/config/ssh/authorized_keys`
     1. Only a single SSH private key is currently supported and should be mounted under `/root/.ssh/id.pem`
  1. **extra dependencies**
     1. Additional dependencies can be installed by mounting an additional `bash` script to the container and specifying its path with the `$USER_INSTALL_SCRIPT` environment variable.
