# Deployment options
There are several possibilities of the computing environment in which the back-end lives. We have to find the sweet spot between limiting applicability and effort required to implement them.

## Single virtual machines
Advantages:
- no new communication mechanism required
- low communication overhead
- very easy tearing tear-down - resize - instantiate workflow

Disadvantages:
- limited to 128 processors (but MPI can oversubscribe)
- depending on the dimensionality of the sampling problem, memory can be an issue

## Several virtual machines
Advantages:
- unlimited scaling
- no new communication mechanism required
- still quite easy to tear-down - resize - instantiate

Disadvantages:
- not fault-tolerant: when using MPI, failure of one machine will kill the whole job

## Kubernetes cluster (with MPI communication)
Advantages:
- unlimited scaling
- no new communication mechanism required

Disadvantages:
- not fault-tolerant: when using MPI, failure of one machine will kill the whole job
- slightly more complex to tear-down - resize - instantiate

## Kubernetes cluster (with different communication method)
Advantages:
- unlimited scaling
- fault-tolerant

Disadvantages:
- development time need to implement new communication method
- slightly more complex to tear-down - resize - instantiate
