# RESAAS: Replica Exchange sampling as-a-service
RESAAS is a web service which helps you sample from multimodal probability distributions. In the context of Bayesian statistics, they arise in the case of unidentifiable parameters which are due to some symmetry in the model or if you have ambiguous data.

## High-level overview
Also see the [announcement blog post](link).  

RESAAS is essentially a Replica Exchange ([Wikipedia](https://en.wikipedia.org/wiki/Parallel_tempering), [blog post](https://www.tweag.io/blog/2020-10-28-mcmc-intro-4/)) implementation with automated tuning and support for cloud computing platforms providing the necessary parallel computing power. 
In a nutshell, Replica Exchange is a Markov chain Monte Carlo (MCMC)  algorithm that works by simulating a series of increasingly "flatter" versions of a probability distribution with a "local" MCMC algorithm such as Hamiltonian Monte Carlo ([blog post](https://www.tweag.io/blog/2020-08-06-mcmc-intro3/)) and occasionally exchanging states between all those simulations.
That way, the Markov chain that samples the distribution of interest can escape from modes it is otherwise likely to be trapped in. 
Replica Exchange requires the choice of a series of probability distributions, which interpolate between the target distribution and some very easy to sample, "flat" distribution.
It is convenient to choose a parameterized family of "tempering" distributions and then vary its parameter to set a "schedule".
RESAAS automagically finds appropriate schedules via an iterative algorithm which results in approximatively constant acceptance rates between neighboring distributions. 
If configured to make use of a cloud computing platform, RESAAS will then automatically create computing resources to run the highly parallel sampling on.
**Be aware that this incurs costs**.
The maximum number of replicas and hence the maximum number of compute nodes can be set by the user.  

The user has to provide a Python module from which the probability distribution they want to sample and a first initial state is imported at runtime.
The interface is specified in [./docs/probability_definition].  

RESAAS offers a web client interface for submission of sampling jobs, but can also be talked to via a RESTful API. The controller component, which performs a single sampling job, can be used stand-alone on a single machine for either development / testing purposes or to solve less demanding multimodal sampling problems.  

RESAAS consists of several components as sketched out in the following schema:
![RESAAS service architecture](./images/service_architecture.png)

The job controller, the client and the scheduler are separate applications and can be found in the `app/` directory.
The runners, schedule estimation logic and shared code can be found in the `lib/` directory.
All applications and library components have detailed READMEs and might be reused outside of RESAAS (especially the schedule estimation logic is applicable to other Replica Exchange implementations as well). 
The `docs/` directory contains more in-depth documentation on configuring RESAAS components, the full set of sampling parameters setable via the REST API and algorithmic details of the automatic schedule estimation.

## Deployment options

RESAAS can be deployed in various ways:

### Fully local execution

For quickly getting your feet wet with RESAAS, it might be simplest to use the controller app locally, see the instructions [here](./app/controller/README.md).
You can also run the example `docker-compose` stack provided in the [./examples](./examples) directory, which very much simulates what happens when RESAAS is deployed to the cloud.

### Local apps, cloud resources

For more demanding one-off sampling jobs, we recommend you deploy the RESAAS applications `docker-compose` stack found in [./docker](./docker) and configure it such that cloud computing resources (virtual machines, storage) are used.
See the walkthrough in [./docs/deployment_walkthrough](./docs/deployment_walkthrough) for detailed instructions on how to to that.

### Full cloud deployment

A simple option is to instantiate a single VM, which hosts all apps, database and logging servers.
Details of this depend very much on your cloud provider, so we don't provide specific instructions at this time.

# Contributing

We very much welcome your feedback and own contributions to RESAAS in the form of issues and pull requests!

# License

TODO

Copyright © 2021–present Tweag I/O
