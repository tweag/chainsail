from abc import ABC, abstractmethod


class AbstractTemperedDistribution(ABC):
    """
    Defines the interface for classes which represent tempered versions
    of a probability distribution.
    """

    def __init__(self, pdf):
        self.bare_pdf = pdf

    @abstractmethod
    def log_prob(self, x):
        """
        Log-probability of the tempered distribution.

        Args:
          x: variates of the underlying distribution
        """
        pass

    @abstractmethod
    def bare_log_prob(self, x):
        """
        Untempered "energy", meaning the part of the original distribution that
        is being tempered, but at the value corresponding to the original
        distribution.
        TODO: the name is misleading. We could call it "negative energy" instead.

        Args:
          x: variates of the underlying distribution
        """
        pass


class BoltzmannTemperedDistribution(AbstractTemperedDistribution):
    """
    Tempers a probability density by transforming it into a Boltzmann
    distribution.

    For a physical system with potential energy E, the configurational part
    (meaning, independent from the momenta) of the Boltzmann distribution is
    given by q(E|beta) \propto exp(-beta * E). Here, beta is, up to a constant,
    the inverse temperature of the system of a heat bath the system is assumed
    to be coupled to. For any probability distribution p(x), we can define a
    pseudo-energy E(x) by E(x) = -log p(x). We can thus use the Boltzmann
    distribution to modify the "ruggedness" (height of modes) of p(x) via beta:
    for beta = 0; q(E(x)) becomes a uniform distribution, while for beta = 1,
    q(E(x)) = p(x). Intermediate beta values can thus be used to create a
    sequence of distributions that are increasingly easier to sample.
    """

    def __init__(self, pdf, beta=1.0):
        """
        Initalizes a Boltzmann distribution for a fake physical system defined
        by a probability density.

        Args:
            pdf(AbstractPdf): object representing a probability distribution
            beta(float): inverse temperature in the range 0 < beta <= 1
        """
        super().__init__(pdf)
        self.beta = beta

    def log_prob(self, x):
        """
        Log-probability of the Boltzmann distribution.

        Args:
            x: variate(s) of the underlying PDF
        """
        return self.beta * self.bare_pdf.log_prob(x)

    def gradient(self, x):
        """
        Gradient of the Boltzmann distribution's log-probability.
        Currently not used.

        Args:
            x: variate(s) of the underlying PDF
        """
        return self.beta * self.bare_pdf.gradient(x)

    def bare_log_prob(self, x):
        """
        Log-probability of the underlying probability density.

        This is required for multiple histogram reweighting.

        Args:
            x: variate(s) of the underlying PDF
        """
        return self.bare_pdf.log_prob(x)


class LikelihoodTemperedPosterior(AbstractTemperedDistribution):
    """
    This wraps an object representing a posterior probability into a
    distribution with a tempered likelihood.

    For a posterior probability, we have, according to Bayes' theorem,
    p(x|D) \propto p(D|x) * p(x) = L(x) * p(x) with the likelihood function
    L(x) and the prior p(x). This tempered distribution family adds an
    inverse temperature-like parameter (see the docstring of
    BoltzmannTemperedDistribution) to the likelihood, while leaving the
    prior untouched. This allows to gradually switch on / off the data
    in the course of a Replica Exchange schedule.

    The ``posterior`` argument is expected to expose the following methods:
    - log_likelihood,
    - log_prior,
    each taking a single argument (the parameters of the model).
    """

    def __init__(self, posterior, beta=1.0):
        """
        Initalizes a likelihood-tempered wrapper.

        Args:
            posterior: object representing a posterior distribution
            beta(float): inverse temperature (in the range 0 < beta <= 1)
              for the likelihood
        """
        self.bare_pdf = posterior
        self.beta = beta

    def log_prob(self, x):
        """
        Log-probability of the likelihood-tempered posterior.

        Args:
            x: variate(s) of the underlying posterior
        """
        return self.beta * self.bare_pdf.log_likelihood(x) + self.bare_pdf.log_prior(x)

    def log_prob_gradient(self, x):
        """
        Gradient of the likelihood-tempered posterior log-probability.
        Currently unused.

        Args:
            x: variate(s) of the underlying posterior
        """
        return self.beta * self.bare_pdf.log_likelihood_gradient(x) + self.bare_pdf.log_prior_gradient(x)

    def bare_log_prob(self, x):
        """
        Untempered likelihood.

        This is required for multiple histogram reweighting.

        Args:
            x: variate(s) of the underlying POSTERIOR
        """
        return self.bare_pdf.log_likelihood(x)
