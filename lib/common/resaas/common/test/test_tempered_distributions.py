import unittest

import numpy as np

from resaas.common.tempering.tempered_distributions import (
    BoltzmannTemperedDistribution,
    LikelihoodTemperedPosterior,
)
from resaas.common.pdfs import AbstractPDF


class FakePDF(AbstractPDF):
    def log_prob(self, x):
        return x[0]

    def log_prob_gradient(self, x):
        return -2 * x


class FakePosterior(AbstractPDF):
    def log_prior(self, x):
        return 2 * x

    def log_prior_gradient(self, x):
        return x

    def log_likelihood(self, x):
        return 3 * x

    def log_likelihood_gradient(self, x):
        return -4 * x


class TestBoltzmannTemperedDistribution(unittest.TestCase):
    def setUp(self):
        self._beta = 2.0
        self._btd = BoltzmannTemperedDistribution(FakePDF(), self._beta)

    def testLogProb(self):
        x = np.array([5])
        result = self._btd.log_prob(x)
        expected = self._beta * x
        self.assertEqual(result, expected)

    def testLogProbGradient(self):
        x = np.array([5])
        result = self._btd.log_prob_gradient(x)
        expected = -2 * self._beta * x
        self.assertEqual(result[0], expected[0])

    def testBareLogProb(self):
        x = np.array([5])
        result = self._btd.bare_log_prob(x)
        expected = 5
        self.assertEqual(result, expected)


class TestLikelihoodTemperedPosterior(unittest.TestCase):
    def setUp(self):
        self._beta = 2.0
        self._ltp = LikelihoodTemperedPosterior(FakePosterior(), self._beta)

    def testLogProb(self):
        x = np.array([5])
        result = self._ltp.log_prob(x)
        expected = 40
        self.assertEqual(result, expected)

    def testLogProbGradient(self):
        x = np.array([5])
        result = self._ltp.log_prob_gradient(x)
        expected = np.array([-35])
        self.assertEqual(result[0], expected[0])

    def testBareLogProb(self):
        x = np.array([5])
        result = self._ltp.bare_log_prob(x)
        expected = 15
        self.assertEqual(result, expected)
