Interface for tempered distribution families supported by Chainsail and two implementations:
- `BoltzmannTemperedDistribution`: for an arbitrary (unnormalized) probability density $p(x)$, introduces an inverse temperature $\beta$ via $p_{\beta}(x) = p(x)^{\beta}$.
- `LikelihoodTemperedPosterior`: for a Bayesian posterior distribution $p(x|D) \propto p(D|x) \times p(x)$, applies an inverse temperature to the likelihood only via $p_{\beta}(x|D) \ propto p(D|x)^{\beta} \times p(x)$.
