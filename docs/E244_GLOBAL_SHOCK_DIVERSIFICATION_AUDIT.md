# E244 | Cross-family global shock falsifies unconditional diversification protection

**Executed:** 2026-10-25. **Domain:** abstract synthetic Bernoulli replay-risk models only. **No real replay evidence or unauthorized testing.**

## Question and falsifiable prediction

E225 showed that spreading eight identical p=0.5 candidates across independent families improved the lower tail under an assumed within-family dependence law. But does that advantage survive **a common shock shared across otherwise independent families**?

## Exact marginal-preserving model

With probability `q` (analyst-assumed), draw one `G ~ Bernoulli(p)` and set all eight outcomes to G. Otherwise use E225's independent-family distribution. Each candidate still has marginal success p, and E[K]=8p=4 for every partition and q. Exact distribution:

`P_q(K=k) = (1-q) P_family(K=k) + q[(1-p)1(k=0) + p1(k=8)]`.

Thus `P_q(K=0) >= q(1-p)` regardless of family diversification. The assumption is deliberately adversarial; **q is not a measured evaluator-outage probability**.

Frozen partitions: [8], [4,4], [2,2,2,2], [1,1,1,1,1,1,1,1]. Frozen q: 0, .01, .05, .10, .25, .50, 1. Within-family E225 strength=0; p=.5. Exact convolution and independent seeded event-level Monte Carlo, 12,000 trials per scenario, 28 scenarios.

## Exact analytical results (not empirical measurements)

| Assumed q | P(K=0), one family [8] | P(K=0), eight independent families |
|---:|---:|---:|
| 0 | 0.05006409 | 0.00390625 |
| 0.01 | 0.05456345 | 0.00886719 |
| 0.05 | 0.07256088 | 0.02871094 |
| 0.10 | 0.09505768 | **0.05351563** |
| 0.25 | 0.16254807 | 0.12792969 |
| 0.50 | 0.27503204 | 0.25195312 |
| 1 | 0.50000000 | 0.50000000 |

**Decisive counterexample:** A diversified portfolio with q=.10 has a larger catastrophic zero-success risk (0.053515625) than the *clustered* portfolio under q=0 (approximately 0.05006409), even though all eight marginals and both expected means remain identical.

At q=1, family assignment is irrelevant: all portfolios have P(K=0)=.5 and lower-decile expected successes 0. The diversification benefit therefore requires a credible independence assumption across families.

## Validation and claim boundaries

Executable code: `experiments/e244_global_shock_diversification.py`. Independent controls: `tests/test_e244_global_shock_diversification.py`. GitHub Actions on draft PR #10 runs Ruff, full pytest, public pinned-SDK parity and exact E244 experiment, archiving JSON receipt.

**SUPPORTED:** exact synthetic counterexample and algebraic lower bound under the stated mixture law. **NOT YET PROVEN:** that any real replay families share this shock, its frequency, evaluator advantage, or generalization to legitimate replay corpora.

**Next:** obtain authorized replay-family observations, estimate cross-family covariance and common-mode failures with uncertainty intervals, compare independence versus global-shock models on frozen held-out families. Do not infer operational attack capability from this abstract result.
