# E507: Copula family changes the synthetic replay-policy conclusion

**Date:** 2 November 2026. **Status:** SUPPORTED in frozen synthetic replay-latency scheduling only; actual replay-latency dependence, empirical utility and external benchmark transfer **NOT YET PROVEN**.

## Question that can change our belief

E487 established a DP50-vs-exact400 policy crossover under a Bernoulli mixture of independent and perfectly shared uniform latency multipliers. Is **pairwise correlation plus identical marginals** sufficient to predict the crossover, or does the *dependence family itself* change the answer?

## Frozen controls

- Reuse the E487 24-option LCG fixture and E455/E473 exact400, exact360, DP50, DP100 and chance90 selection algorithms, without task-specific optimization or attack payloads.
- New deterministic seed cohort **896–1023 (128 seeds)**; **256 normal draws per seed**, reused across copula families and q settings to reduce variance.
- Nominal replay budget 400; realized utility = completed-prefix reward minus 50 if truncated.
- Every individual latency multiplier has the same theoretical **U[0.7, 1.3]** marginal for both copula families.
- Both families have the same **pairwise Pearson correlation q**. Bernoulli: with probability q all factors share one uniform draw, otherwise independent uniforms. Gaussian: `Z_i = sqrt(rho) Z_shared + sqrt(1-rho) Z_i_ind`, `U_i = Phi(Z_i)`, `rho = 2 sin(pi q/6)`. For normal copulas, `Corr(Phi(Z_i), Phi(Z_j)) = (6/pi) asin(rho/2) = q`.
- Exact q=0 and q=1 endpoint handling avoids a floating-point near-one root artifact found and corrected during local unit testing.
- No real evaluator, security payloads, private data or third-party requests.

## Result: same marginal and correlation, different policy ranking

Mean **DP50 minus exact400** utility (positive favors DP50):

| Target Pearson q | Gaussian copula | Bernoulli mixture |
|---:|---:|---:|
| 0 | -19.7549 | -19.7549 |
| 0.25 | -7.3512 | -12.2785 |
| 0.40 | -2.5623 | -7.7927 |
| 0.50 | +0.2064 | -4.8021 |
| **0.55** | **+1.4202** | **-3.3069** |
| 0.60 | +2.5513 | -1.8116 |
| 0.675649 | +4.0404 | +0.4507 |
| 0.75 | +5.5666 | +2.6742 |
| 1 | +10.1506 | +10.1506 |

At q=0.55, descriptive across-seed 95%-style intervals are **Gaussian +0.041 to +2.799**, **Bernoulli -4.797 to -1.817**. Their paired Gaussian-minus-Bernoulli difference is **+4.7271** with descriptive interval **+3.990 to +5.464**. These are not inferential population confidence intervals; the seeds and distributions are synthetic.

**Falsification:** A single correlation coefficient and matching marginal latency distributions do **not** determine the sign of DP50-vs-exact400 policy advantage. The copula family matters. A simple correlation-calibrated policy can be confidently wrong in this model.

The q=0.5 Gaussian advantage is too small relative to descriptive uncertainty to call a stable win. At q=0.55 the sign difference is stronger in this frozen cohort. The Bernoulli crossing on these new seeds is between q=0.60 and 0.675649; the Gaussian crossing is between q=0.40 and 0.55. Do not present these coarse brackets as exact population thresholds.

Across the tested grid, DP100's worst **mean** advantage relative to exact400 is about **+0.0090** at q=0, while its interval includes losses; this is a candidate robust policy, not proof of superiority. Chance90 loses on all tested settings.

## Reproduction

```bash
python research/e507_gaussian_copula.py > e507_result.json
python -m unittest discover -s research -p 'test_e507_gaussian_copula.py' -v
```

Seven controls cover deterministic fixture, exhaustive exact knapsack oracle, exhaustive DP expected-value oracle, analytical correlation mapping, independent/shared endpoints, empirical q=0.5 correlation, and fresh-cohort sign reversal. The first local test run **failed** at the q=1 floating-point endpoint; this was corrected before committing and the rerun passed 7/7. Preserve this failure evidence.

## Limits and next gate

Synthetic latency multipliers are not actual replay timing data. Matching pairwise correlation does not match higher-order dependence, which is precisely the variable under test. Normal CDF and finite Monte Carlo introduce small numerical/sampling error. No hidden/private evaluator was queried.

**Next:** adversarial fixed-marginal copula families, tail-risk/CVaR and worst-case regret comparisons on fresh seeds; only then legitimate empirical latency observations with provenance. Do not optimize security attack payloads or bypass guardrails.
