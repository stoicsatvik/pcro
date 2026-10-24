# E204 — Family dependence changes tail risk without changing marginal forecasts

**2026-10-24; synthetic research only.** Independent closed-form binomial-mixture calculation plus 40,000 seeded Monte Carlo trials per setting. Run `python experiments/e204_family_tail_risk.py`. Eight candidates share one family; each has success probability 0.5, unit reward, deterministic unlimited replay budget and distinct novelty cells. This experiment is about probability modelling, not constructing any replay attacks.

The E184 marginal-preserving law chooses a common uniform with probability `w = 0.5/sqrt(1+s)`, where `s` is the *concentration* argument called `family_correlation_strength` in the current API. Conditional on shared U below p, success probability is `q_hi=w+(1-w)p`; otherwise `q_lo=(1-w)p`. Therefore `K | U<p ~ Binomial(n,q_hi)` and `K | U>=p ~ Binomial(n,q_lo)`. This provides an **independent exact distribution** of the number of successes, without relying on the replay simulator implementation.

| concentration s | pairwise corr w² | E[K] | Var[K] | Exact P(K=0) | vs independent |
| ---: | ---: | ---: | ---: | ---: | ---: |
| independent | 0 | 4 | 2 | 0.00390625 | 1.00× |
| 0 | 0.25 | 4 | 5.5 | 0.05006409 | **12.82×** |
| 20 (current default) | 0.0119048 | 4 | 2.166667 | 0.00524727 | **1.34×** |
| 100 | 0.00247525 | 4 | 2.034653 | 0.00417866 | **1.07×** |

Monte Carlo at seed 204024 and 40,000 trials per setting matched the exact distribution with maximum absolute bin errors of 0.00202, 0.00228 and 0.00202 respectively. Eight deterministic pytest controls passed locally.

**Falsification:** identical individual success probabilities and identical expected reward do *not* identify the probability of catastrophic zero-success outcomes. A mean-score-only comparison can therefore conceal tail risk. The model parameter is inverse in its effect: larger `family_correlation_strength` yields *weaker* dependence, so its name must not be interpreted literally as an empirical correlation.

**Claim:** synthetic distribution/tail sensitivity SUPPORTED by exact algebra and independent Monte Carlo. **Real replay dependence NOT YET PROVEN**; no real outcomes or private evaluator were used. Next: estimate within-family covariance on legitimate replay outcomes with uncertainty intervals; compare independence and common-mode models on held-out families, never on hidden/private evaluation.
