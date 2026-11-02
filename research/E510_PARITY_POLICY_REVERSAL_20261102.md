# E510 | Pairwise-identical latency laws reverse a frozen scheduling choice

Date: 2026-11-02. Continuation of E507-E509 on draft PCRO PR #25. This is a **constructed exact synthetic counterexample**, not a measured scheduler result.

## Predeclared decision and falsifiable claim

Freeze two policies for three sequential nominal 100-ms tasks, each worth 10 reward units, with a 300-ms deadline and a 10-unit penalty on the first missed task:

- **Policy A:** attempt all three tasks in order. The first two always complete because their combined worst-case latency is strictly below 260 ms. If task three misses, retain 20 earned units and subtract 10, yielding 10. If all complete, earn 30.
- **Policy B:** attempt only the first two tasks, always finish, earn 20 and incur no miss penalty.

Use E509's two parity copulas, which have identical continuous U[0.7,1.3) marginals and **identical bivariate distributions for every task pair**, not just equal correlations. Neither policy nor its reward/penalty is refitted to the dependence family.

The E509 exact Irwin-Hall calculation gives P(complete three) = 3/8 under even parity, 5/8 under odd parity, and 1/2 under independent factors. Therefore

`E[U(A)] = 10 + 20 P(complete three)`; `E[U(B)] = 20`.

| Synthetic dependence | P(complete all three) | E[U(A)] | E[U(B)] | A minus B |
|---|---:|---:|---:|---:|
| Even parity | 3/8 | 17.5 | 20 | **-2.5** |
| Independent baseline | 1/2 | 20 | 20 | 0 |
| Odd parity | 5/8 | 22.5 | 20 | **+2.5** |

**Result:** A and B reverse their expected-utility ranking even though *all pairwise latency distributions are identical*. The reversal is five synthetic reward units end-to-end, exactly, without sampling error. Matching marginal and pairwise latency diagnostics therefore cannot guarantee a policy ordering.

## Tests and evidence boundary

`research/test_e510_parity_policy_reversal.py` contains four deterministic tests: exact pairwise bit tables, the two-task deadline bound, exact fractional A utilities, and the sign reversal with an independent tie. Locally reconstructed E509 helper functions plus these E510 tests ran with `python -m unittest discover -s research -p 'test_e510_parity_policy_reversal.py' -v`: **4/4 passed**. The reconstructed helper is algebraically equivalent to E509 but local execution was not a full repository checkout. The E509 workflow is updated to execute both E509 and E510 tests on GitHub Actions; its result must be checked separately.

This extends E509 from a **deadline-probability** counterexample to a **fixed-policy ranking** counterexample. It does not reproduce E507's 24-task q=0.55 reversal, identify the actual latency copula, validate empirical replay, or show that a single tail statistic predicts performance on held-out families. The utility formula makes the completion statistic predictive *by construction* here; do not present that as an out-of-sample model.

**Next falsification gate:** freeze a non-tautological prefix-tail feature and a predictor before generating held-out 24-task copulas and seeds, compare its prediction against marginal/pairwise-only baselines, and preserve failures. No real latency data, evaluator access, external outreach, deployment, or merge.
