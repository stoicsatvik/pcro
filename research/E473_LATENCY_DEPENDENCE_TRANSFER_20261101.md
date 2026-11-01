# E473 | Frozen policy transfer across latency-dependence and tail families

**Date:** 2026-11-01. **Scope:** deterministic synthetic scheduling. No evaluator access, security payload, third-party action, or competition submission.

## Question

E455 showed that the penalty-50 expected-prefix dynamic program can outperform nominal exact packing under a fully shared U[0.7,1.3) latency multiplier but fail under independent shocks. Does this reversal replicate on a new untouched seed range and survive a distribution-shifted right tail? Is a more conservative penalty-100 schedule robust?

## Frozen protocol

- Inherit E455's 24-option LCG fixture, density-ordered subsequence DP, 400-unit budget, and fixed policies **exact400, dp50, dp100, chance90**. The evaluated utility is realized completed-prefix reward minus **50** for a truncated schedule, regardless of policy's optimization penalty.
- New untouched fixture seeds **640–767**; **64 deterministic draws per seed**; all policies compared on the **same draws** within each condition. The seed range, policies, penalty and condition grid were selected before reading these results.
- Uniform family: multiplier U[0.7,1.3). Tail family: 90% U[0.7,1.1), 10% U[1.1,2.3), mean **0.98**. This is a **synthetic** distribution, not measured replay latency.
- Dependence interpolation: each option's multiplier = (1-rho)*independent + rho*common, rho in **0, 0.25, 0.5, 0.75, 1**. **Important confound:** interpolation changes variance and marginal distribution as well as dependence. Rho is a mixing coefficient, **not** a Pearson correlation estimate; only rho=0 and rho=1 preserve the original per-family marginals.
- Paired differences are averaged first across draws per seed; reported uncertainty is a descriptive 1.96×SE interval over 128 seed-level differences, not a population-calibrated or preregistered significance test. No tuning after evaluation.

## Source-exact result: utility difference versus nominal exact400

| Latency family | Mixing rho | dp50 delta [approx 95% seed interval] | dp100 delta [approx 95% seed interval] |
| --- | ---: | ---: | ---: |
| Uniform | 0 | **-21.835** [-24.285,-19.386] | +1.535 [-1.437,+4.507] |
| Uniform | 0.25 | **-22.236** [-24.518,-19.955] | +1.256 [-1.540,+4.053] |
| Uniform | 0.5 | **-10.981** [-12.836,-9.127] | +2.937 [+0.746,+5.127] |
| Uniform | 0.75 | +1.313 [-0.066,+2.691] | +1.021 [-0.618,+2.660] |
| Uniform | 1 | **+8.731** [+7.468,+9.994] | -2.067 [-3.710,-0.425] |
| Tail | 0 | **-16.140** [-18.474,-13.806] | **-8.882** [-11.491,-6.272] |
| Tail | 0.25 | **-16.784** [-18.975,-14.592] | **-9.557** [-12.208,-6.906] |
| Tail | 0.5 | **-12.335** [-14.212,-10.459] | **-13.200** [-16.306,-10.094] |
| Tail | 0.75 | +0.407 [-1.130,+1.943] | **-11.821** [-14.946,-8.695] |
| Tail | 1 | **+9.983** [+8.389,+11.577] | **-10.350** [-13.348,-7.353] |

The **same frozen dp50 policy** wins under the shared multiplier but loses decisively under independent multipliers, including the new right-tail family. The penalty-100 policy does **not** provide distribution-free protection: it loses in all five tail scenarios. The 90%-completion chance-constrained policy also loses against nominal exact packing in every tested condition; it trades utility for a low modeled truncation rate.

**Falsification:** shared-latency-model policy superiority does not transfer to independent-shock or tail-shifted families under this frozen synthetic utility. This is a failure of **model transfer**, not proof of an optimal alternative.

## Validation and limits

- Source: `research/e473_latency_dependence_transfer.mjs`; machine-readable full 10-condition receipt: `research/results/e473_latency_dependence_transfer_20261101.json`.
- The exact fetched GitHub source blob was executed in an isolated V8 engine after substituting equivalent local `node:assert/strict` assertion methods for its import. **12 exhaustive 8-option DP oracles**, survival boundaries, factor domain, shared-factor and deterministic reproducibility checks passed.
- This is **not native Node execution** and **not exact-head GitHub Actions CI**. The inherited PCRO Ruff/pytest/property workflows were not rerun for this branch.
- All data are synthetic. There are no authorized measured replay timings, no measured latency dependence, no real-world scheduling benefit and no external evaluator interactions.
- The tail family has a different mean from uniform, and intermediate rho conditions alter variance. The experiment cannot attribute intermediate effects to correlation alone.

## Claim state and next gate

**SUPPORTED in frozen synthetic source-exact tests:** a material dependence-family reversal of penalty-50 utility, and negative transfer of penalty-100 under tail shocks.

**NOT YET PROVEN:** robust policy superiority, external scheduling performance, generalization to independent real latency generators, or security evaluator outcomes.

**Next decisive test:** use a *marginal-preserving* dependence generator (e.g. rank/copula mixing) to separate correlation from variance; add an independent heavy-tail family with matched mean and quantiles; preregister robust/minimax-regret and CVaR policies on a new untouched seed range. Compare against simple conservative capacity caps. Seek authorized measured latency only when legitimately accessible.

No main merge, paid API, deployment, outreach or irreversible external action.
