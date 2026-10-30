# E426 | Nominal exact packing versus realized fixed-prefix reward

**Date:** 2026-10-30. **Scope:** synthetic abstract replay candidates only. No prompt injection, real targets, guardrail bypass, actual replay or competition evaluation.

## Falsifiable question

E406 rejected the claim that density packing always maximizes deterministic additive reward. Does replacing density greedy with an exact nominal 0/1 knapsack oracle necessarily improve realized reward when replay latency varies and the evaluator stops at the first item that exceeds its fixed budget?

**No, in this predeclared synthetic model.** Nominal exact selection wins on nominal value but loses on average realized fixed-prefix reward under independent bounded latency uncertainty.

## Frozen protocol

- E406's unchanged 32-bit LCG generator, held-out seeds **128–255** (128 seeds), **24** candidates each, integer reward 5–100 and nominal cost 10–120 ms.
- Fixed evaluation budget **400 ms**. Compare the actual `ReplayScheduler.pack_for_budget` with exact integer-ms 0/1 DP, both using production robust-density order for their selected fixed prefix.
- Per seed **64** deterministic independent latency draws. For each candidate, realized cost = nominal cost × a pseudorandom factor in **[0.7, 1.3)**. Noise uses a separate frozen 32-bit LCG and seed/draw mixing; it is not inferred from actual replay data.
- Compare nominal packing at 100% budget and a prespecified 85% (340 ms) cost cap. The latter is a sensitivity control, not a tuned optimum.
- Each draw reuses the same candidate-specific latency factors across methods. The evaluator executes a fixed list and stops at the first over-budget candidate, never skipping ahead.
- Exact DP is valid for the **nominal integer additive model only**, not for stochastic or correlated latency. No training, prompt generation or hidden-test access.

## Results

| Method | Mean nominal reward | Mean realized reward | Fixed-prefix truncation |
|---|---:|---:|---:|
| Density greedy, 400 ms | 657.515625 | **642.452271** | 30.8716% |
| Nominal exact DP, 400 ms | **664.578125** | 639.470703 | 40.3320% |
| Density greedy, 340 ms cap | 598.242188 | 598.205566 | 0.0732% |
| Nominal exact DP, 340 ms cap | 603.734375 | 603.623779 | 0.1953% |

Across 128 paired seed means, nominal exact minus density greedy realized reward = **−2.981567**. Exact wins 17 seeds, loses 48, ties 63. The tie-heavy result means this is not a claim of universal greedy superiority. The 85% margin reduces truncation but also gives up considerable expected reward; it is not an optimized robust policy.

**Independent local validation:** A source-equivalent Python scheduler mirror and an independently authored JavaScript implementation agree exactly on all four frozen receipts, truncation rates and 128 paired seed comparisons. A separate 12-candidate exact DP implementation was checked against brute-force enumeration for three held-out seeds and three budgets (nine agreements). The committed test file includes four tests, but **exact committed-source pytest, Ruff and GitHub Actions were NOT RUN**. The repository previously reported exhausted included Actions minutes; no paid CI was requested.

## Interpretation

- E406's **nominal density optimality** remains REJECTED for the deterministic additive model.
- The stronger inference that **nominal exact selection necessarily dominates realized fixed-prefix reward** is REJECTED for this synthetic bounded-latency counterexample.
- A reliable real-world policy, robust chance-constrained optimizer, runtime-tail model and generalization to actual authorized evaluator replay remain **NOT YET PROVEN**.
- The 30% independent noise model is deliberately hypothetical. It is not an observed latency distribution, and this result does not measure attack success.

## Next experiment

Freeze legitimately collected, authorized replay-latency distributions and an independent held-out candidate set; compare density, nominal exact, and conservative chance-constrained selectors under equal budget and fixed-prefix semantics. Include correlated tail stress, cost-calibration error, runtime/memory and the effect of score-cell dependence. Do not modify production scheduling based on synthetic data alone.

## Reproduce

```bash
python -m research.e426_latency_uncertainty
pytest -q tests/test_e426_latency_uncertainty.py tests/test_e406_prefix_knapsack_gap.py
ruff check research/e426_latency_uncertainty.py tests/test_e426_latency_uncertainty.py
```

This experiment is research-only and stacked on E406. No production scheduler, main branch, infrastructure, external systems or paid API was changed.
