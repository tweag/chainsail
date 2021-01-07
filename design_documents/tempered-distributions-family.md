# Families of tempered distributions supported by RESAAS
There are, to the best of my knowledge, two families of tempered distributions we can easily support and which are universal to sampling / Bayesian data analysis problems.
I'll describe both in the following, but for the very first PoC, we restrict RESAAS to support only the Boltzmann distribution.
The two-Boltzmann-chains family can be relatively easily added later (TODO: think how easy schedule optimization actually is...)

## Family of Boltzmann distributions
The Boltzmann distribution is a probability distribution of the form `p(x|beta)=exp(-beta * E(x))` and is thus parameterized by the "inverse temperature" `beta`.
In physics, `E` is the physical system's energy, but in general, we can, given any probability distribution `p(x)`, define a pseudo-energy by `E(x)=-log p(x)`.
This translates to a tempered family of distributions `p(x|beta)=p(x) ^ beta`.
For `beta=1`, we recover the original probability distribution, while for `beta=0`, we end up with a uniform "distribution" with infinite support.
The tempered family of distributions then consists of distributions `p(x|beta)` with `0 < epsilon <= beta <= 1`. 
The replica schedule to be optimized is then given by the sequence of `beta`s.

## Separate Boltzmann distributions for likelihood and prior
In Bayesian inference, we have `p(x|D) ~ p(D|x) * p(x)` with `~` denoting proportionality.
`p(x|D)` is the posterior distribution and usually what a RESAAS user wants to sample.
It is proportional to the product of likelihood function `p(D|x) =: L(x)` and prior `p(x)`.
Now, in case of really bad luck, not only the likelihood might give rise to multimodality, but the prior itself is already multimodal.
For these cases, we can introduce a two-dimensional Replica Exchange schedule with two inverse temperatures `lambda` and `beta`.
`lambda` determines the influence of the likelihood and `beta` the influence of the prior, so that we have a two-parameter family of distributions `p(x|lambda, beta) ~ L(x) ^ lambda  *  p(x) ^ beta`.
The idea then is to build a schedule consisting of two subschedules:
To get an easy-to-sample distribution, we set `lambda=0` and `beta=epsilon > 0`.
In the first subschedule, we increase `beta` from `epsilon` to one while keeping `lambda=0`.
In the second subschedule, we keep `beta=1` and slowly increase `lambda` from zero to one, until we eventually arrive, with `lambda=beta=1` at the posterior distribution.

## Further ideas
At one point, we can also support the [Tsallis ensemble](https://en.wikipedia.org/wiki/Q-exponential_distribution), which has the neat property to also spread out modes instead of just modifying there "height".

## Arbitrary families
In principle, we can also support arbitrary, user-defined families of distributions.
For the sampling, this is totally trivial.
Only the schedule optimization is slightly more involved then.
