# E454 | Exact expected-prefix DP under synthetic shared latency (31 October 2026)

## Hypothesis and frozen design
E441 showed that the ranking of nominal-exact and density-greedy schedulers reverses under shared synthetic latency. Instead of assuming that the nominal 400-ms packing optimum also maximizes **expected realized fixed-prefix reward**, optimize the latter exactly for a **density-ordered subsequence** under one common multiplier U~Uniform[0.7,1.3). For a prefix with cumulative nominal cost C, the exact probability of completion is q(C)=clip((400/C-0.7)/0.6,0,1). Expected realized reward is Σ reward_j × q(C_j), so an integer-cost dynamic program over ordered subsequences maximizes that objective. It is **not** globally optimal over all permutations, nor calibrated to real latency.

Predeclare E441 seeds 128..255 as an exact regression control and **independent, untouched seeds 256..383** as the new holdout, with 64 deterministic draws per seed. Compare unchanged greedy/exact 400 and 340 nominal cap policies, plus the new shared-expectation DP. Evaluate all five fixed policies on independent, half-shared and fully shared synthetic noise. The half-shared family changes marginal variance, not only dependence.

## Executed results

| Seed population / noise | Nominal exact 400 | Shared-expectation DP | DP minus exact | Paired seed wins/losses/ties | DP truncation |
|---|---:|---:|---:|---|---:|
| 128–255 / independent | 639.471 | 643.024 | 3.553 | 77/43/8 | 100.00% |
| 128–255 / half_shared | 634.793 | 644.320 | 9.526 | 106/18/4 | 100.00% |
| 128–255 / fully_shared | 624.395 | 651.011 | 26.616 | 128/0/0 | 95.03% |
| 256–383 / independent | 644.334 | 647.529 | 3.195 | 80/34/14 | 100.00% |
| 256–383 / half_shared | 641.104 | 650.627 | 9.524 | 110/16/2 | 100.00% |
| 256–383 / fully_shared | 631.678 | 659.365 | 27.688 | 128/0/0 | 95.01% |

Exact analytic shared-model expectations on the holdout: nominal exact 400 = 630.7891, shared-expectation DP = 658.1106. The held-out fully shared 64-draw means differ from these exact expectations because the deterministic pseudo-random draws are finite, not because the expectation formula was fitted to the holdout.

## Tests and limitations
- Four independent 8-option exhaustive subset enumerations agree with the density-ordered DP to 1e-8; two exact probability-boundary assertions pass.
- The script reproduces four frozen E441 baseline mean rewards **exactly** (independent and fully shared, greedy/exact 400), providing a cross-implementation regression control.
- 128 control + 128 held-out seeds × 64 draws × three noise modes × five fixed policies were evaluated, with paired seed as the statistical unit; 8,192 draws per population/mode are not independent evidence.
- The DP's ~95% truncation in fully shared mode is **expected by construction**: it maximizes accumulated prefix reward, not probability of finishing the entire schedule. It may be unsuitable if the evaluator imposes an all-or-nothing completion requirement, failure penalty, score-cell dependence or external costs.
- These are **synthetic additive rewards**, with known common-shock distribution, no measured timing, no real evaluator replay, no security payload, no platform interaction, no production policy changes. Holdout seeds are independent of E441's seed range but drawn from the **same generator family**.

## Claim state
**SUPPORTED IN REPRODUCIBLE SYNTHETIC TESTS:** an exact expected-prefix objective can outperform nominal exact packing on both frozen and new generator seeds when shared latency assumptions hold. **NOT YET PROVEN:** empirical timing calibration, out-of-family transfer, real evaluator utility, general scheduler superiority or safety of deployment. No external blocking claim: real authorized timing measurements are still required for empirical validation, but computational avenues remain open.

## Next decisive experiment
Freeze independent candidate-cost and latency-family generators (not merely new seeds); compare expected-prefix DP against chance-constrained and risk-penalized controls under misspecified common shocks, varying the cost of truncation. Seek legitimate, consented public replay timing traces and measure batch correlation before any production promotion.

Reproduce without dependencies: `node research/e454_shared_latency_expected_dp.mjs`. No Actions run requested or main merge.
