# docker

`docker-compose` can be used to spin up a full Chainsail deployment.

Before running it, you need to build the images:
```
docker build -t "chainsail-celery-worker:latest" -f ./celery/Dockerfile ../
docker build -t "chainsail-scheduler:latest" -f ./scheduler/Dockerfile ../
docker build -t "chainsail-nginx:latest" -f ./nginx/Dockerfile ../
docker build -t "chainsail-client:latest" -f ../app/client/Dockerfile ../app/client/
```

If you get errors about missing permissions to pull those images, you need to build them with tags locally.

## client

TODO

## scheduler

Docker image containing the scheduler app behind a uWSGI app server and an NGINX reverse proxy.

## celery-worker

Docker image containing the celery worker.

## node

Docker image containing all dependencies required to run resaas job nodes, including 
`controller`. 

Accepts the following configurations:

  1. **ssh**
     1. SSH public keys can be specified by mounting an authorized_keys file to `/app/config/ssh/authorized_keys`
     1. Only a single SSH private key is currently supported and should be mounted under `/root/.ssh/id.pem`
  1. **extra dependencies**
     1. Additional dependencies can be installed by mounting an additional `bash` script to the container and specifying its path with the `$USER_INSTALL_SCRIPT` environment variable.
