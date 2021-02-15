# examples

Example docker-compose stacks for running parts of the resaas system locally. 

The examples depend on the configuration files in [./config](./config), which you must manually populate with the required secrets.

## job

`controller` stack for executing a single test job locally using rexfw + openMPI. 

To run this stack, update the ssh volume mounts in the docker-compose file locally to point to ssh keys on your machine. It is recommended to create new keys for development purposes (instead of using one of your current keys).

```shell
$ docker-compose --file job/docker-compose.yaml build
$ docker-compose --file job/docker-compose.yaml up
```
