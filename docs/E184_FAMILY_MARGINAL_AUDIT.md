# E184 — Family-shock marginal falsification (2026-10-24)

## Hypothesis and falsification target

The replay simulator should preserve each candidate's stated Bernoulli success
probability, including 0 and 1, while modelling positive within-family dependence.
Its original beta-family shock blended each candidate's probability with a
draw centered on the *family mean*. This does **not** preserve individual
marginals when family members have heterogeneous forecasts.

The exact pre-correction expectation is approximately
`E[p'_i] = (p_i + clamp(mean_family, .001, .999)) / 2`.
Thus a family with `p=[.1,.9]` is shifted to `[.3,.7]`. This is a
model defect, not a discovered property of any evaluator.

## Independent synthetic experiment

Run `python experiments/e184_family_marginal_audit.py`.
100,000 independent trials per scenario, seed 1729, strength 20.

| Declared p | Old measured rates | Corrected measured rates |
| --- | --- | --- |
| [0] | [0.00059] | [0.00000] |
| [1] | [0.99953] | [1.00000] |
| [.1,.9] | [.30276,.69805] | [.09988,.90048] |
| [.25,.75] | [.37661,.62201] | [.24926,.75101] |

This table is a synthetic simulation of the old and new laws. It is **not**
a measured JED replay result or an estimate of any private guardrail.

## Correction and interpretation

Each family receives one shared uniform draw per trial. Each candidate
uses that shared uniform with probability
`w = 0.5 / sqrt(1 + family_correlation_strength)`, otherwise it uses an
independent uniform. Both branches compare against the *candidate's own*
probability. Marginals are therefore preserved exactly, and for equal-p
members the Bernoulli correlation is `w²`, approximately matching the
old beta-shock's covariance scale.

This preserves positive common-mode dependence, but the full joint law
differs from the beta mixture. No claim of calibrated real-world correlation
is made. Future measured replay data would be needed to fit it.

## Gates and limits

- Existing reproducibility and timeout regressions remain unchanged.
- New deterministic tests cover p=0/p=1, heterogeneous marginals,
  a rare/high-reward full replay, positive dependence and invalid inputs.
- No hidden benchmark values, third-party targets or real-world attacks used.
- **Claim:** Old heterogeneous marginal model REJECTED by algebra and
  independent synthetic Monte Carlo. Corrected marginal invariant SUPPORTED
  by derivation and tests. Real replay calibration NOT YET PROVEN.
- **Next:** Fit correlation from legitimate replay outcomes with confidence
  intervals and sensitivity across families. Do not optimize against a
  speculative correlation coefficient as though it were measured.
