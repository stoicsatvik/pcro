# E260 | Pairwise covariance cannot identify catastrophic replay tails

Date: 2026-10-25. Scope: exact **abstract** exchangeable Bernoulli mathematics; no attack traces, external evaluator access, or empirical replay measurements.

## Decision-changing question

E244 showed that an *assumed* global-shock mixture can destroy family diversification. Its next proposed step was to estimate cross-family covariance. Is even perfectly known pairwise covariance enough to forecast the probability that **all eight** candidates fail?

**No.** With identical success marginals \\(P(X_i=1)=1/2\\) and exactly zero covariance for **all 28 pairs**, the all-fail probability can range from **0% to 10%** under exchangeability. A fully independent joint law gives only **1/256 = 0.390625%**. Thus an apparently independent pairwise covariance matrix can coexist with a catastrophic tail **25.6 times** the independent forecast.

## Three explicit joint distributions

Let \\(K=\\sum_{i=1}^{8}X_i\\). Conditional on \\(K=k\\), choose a uniformly random k-subset of eight successes. This constructs a valid exchangeable **joint** distribution over all 256 binary outcomes.

| Law | Distribution of K | P(K=0) | Lower 10% mean K |
|---|---|---:|---:|
| Zero-tail extreme | P(K=2)=1/3; P(K=5)=2/3 | **0** | 2 |
| Independent baseline | P(K=k)=C(8,k)/256 | **1/256** | 103/64 |
| Maximum-tail extreme | P(K=0)=1/10; P(K=4)=1/2; P(K=5)=2/5 | **1/10** | 0 |

Every law satisfies E[K]=4 and E[K(K−1)]=14. Exchangeability implies \\(P(X_i=1)=E[K]/8=1/2\\) and \\(P(X_i=X_j=1)=E[K(K-1)]/(8\\cdot7)=1/4\\). Thus **every pair is independent** even though the eight-way joint laws differ.

## Exact upper bound, not a Monte Carlo estimate

For every integer \\(k\\in\\{0,\\dots,8\\}\\),

\\[
\\mathbf{1}[k=0]\\leq \\frac{(k-4)(k-5)}{20}.
\\]

Taking expectations and substituting the frozen moments,

\\[
P(K=0)\\leq \\frac{E[K(K-1)]-8E[K]+20}{20}
=\\frac{14-32+20}{20}=\\frac{1}{10}.
\\]

The maximum-tail law attains this bound. The zero-tail law attains the trivial lower bound 0. A separate exact-Fraction enumeration of all 84 three-point supports finds 31 feasible vertices and independently confirms the extrema. The test suite also enumerates **all 256 outcomes** and checks eight individual marginals and all 28 pairwise joint success probabilities for each law.

Run: `python experiments/e260_pairwise_tail_nonidentifiability.py` and `pytest tests/test_e260_pairwise_tail_nonidentifiability.py`.

## Falsified inference and next measurement

**REJECTED:** "Pairwise zero covariance (even exactly measured) licenses an independent-binomial catastrophic-risk forecast."

**SUPPORTED:** The exact 0–10% bound for eight exchangeable Bernoulli candidates with the stated marginals and pairwise moments.

**NOT YET PROVEN:** Any of these distributions describes real replay outcomes, and no observed empirical risk frequency has been estimated.

**Next:** On legitimately obtained replay-family observations, preserve *joint run identities* and record the eight-way success vector, not only covariance. Compare the observed all-fail rate and higher-order co-failure patterns against the independent forecast and the moment-compatible worst-case bound. Use frozen held-out runs, family-level uncertainty, and calibrated joint-tail intervals. If the corpus is too small, report non-identifiability rather than fitting a confident parametric common-shock weight.

No bypasses, unauthorized security testing, hidden evaluators, private data or deployment.
