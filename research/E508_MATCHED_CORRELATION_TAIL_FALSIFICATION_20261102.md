# E508 | Matched Pearson correlation does not determine joint slowdown tails

Date: 2026-11-02. Continuation of E507 on draft PR #25, with frozen E507 copula generator, target pairwise Pearson correlation q=0.55, and uniform factor marginals U[0.7,1.3]. Synthetic scheduling only; no observed latency, evaluator access, or deployment.

## Falsifiable question

If two latency models have the same one-dimensional marginals and pairwise Pearson correlation, must they assign the same probability to two tasks simultaneously exceeding a 1.2x latency multiplier? **No.**

Let p=P(F>1.2)=1/6 for each uniform marginal. The E487 Bernoulli common-shock construction has exact joint exceedance probability

P(F1>1.2,F2>1.2) = q*p + (1-q)*p^2 = 0.10416666666666667 at q=0.55.

The E507 Gaussian copula uses latent rho=2*sin(pi*q/6) to match the same Pearson correlation of the uniform transforms. The deterministic Monte Carlo check (seed 508, 50,000 bivariate draws, the frozen `gaussian_factors` implementation) produced 8,329 first-factor exceedances and 3,802 simultaneous exceedances:

- Gaussian marginal exceedance: 8329/50000 = **0.16658** (target 1/6).
- Gaussian joint exceedance: 3802/50000 = **0.07604**.
- Gaussian conditional second-factor exceedance given first-factor exceedance: 3802/8329 = **0.45648**.
- Bernoulli exact conditional exceedance: q + (1-q)*p = **0.625**.

The Bernoulli joint probability is approximately **37% larger** than the Gaussian estimate in this frozen experiment. Both models have the same theoretical marginal and pairwise Pearson correlation; their upper-tail co-movement differs.

## Engineering action

Added a deterministic regression test to `research/test_e507_gaussian_copula.py` that computes the Bernoulli result analytically, samples the frozen Gaussian generator with a separate seed, verifies the marginal tail, and rejects an erroneous assumption that the joint upper-tail probability is determined by correlation alone.

This test is explanatory evidence for E507's opposite policy rankings at q=0.55. It **does not prove** that this one tail statistic causes the utility sign reversal. The scheduling objective also depends on task order, cumulative costs, threshold crossings, and the full joint distribution.

## Negative results and limitations

- Same Pearson correlation does not imply equal simultaneous slowdown probability.
- This does not identify which copula describes any real runtime.
- The Gaussian figure is finite seeded Monte Carlo, not an exact Gaussian integral.
- Threshold 1.2 is a synthetic diagnostic, not a calibrated service-level limit.
- No real-world replay improvement, performance guarantee, or production change is claimed.

Next gate: predeclare a small set of joint-tail and prefix-overrun statistics, then evaluate whether any predicts utility ranking across independently held-out copula families and seeds. Avoid fitting a threshold to the observed E507 sign reversal.
