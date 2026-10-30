# E406 | Density packing versus exact replay-budget oracle

**30 October 2026. Scope:** offline, deterministic, six-candidate abstract
reward/cost laboratory. No prompt injection, target access, attack construction,
private data, guardrail bypass or actual evaluator replay was performed.

## Falsifiable question

The production `ReplayScheduler.pack_for_budget` is explicitly a greedy
pre-replay baseline. Does its reward-density order reliably maximize expected
reward when replay cost is deterministic and all candidate rewards are additive?

**No.** A six-item exact subset oracle finds higher reward in 94 of 384 frozen
synthetic budget cases. This falsifies global optimality of the heuristic, not
its utility or the evaluator's fixed-prefix semantics.

## Protocol

- 128 predeclared LCG seeds, six candidates per seed; independent integer
  reward 5–100 and conservative replay cost 10–120 ms from a fixed 32-bit LCG.
- Three budgets: 100, 160, 220 ms; 384 comparisons.
- Success probability fixed at 1.0, one deterministic latency observation
  per candidate, no novelty or guardrail overlap.
- Compare the unchanged production `pack_for_budget` to exhaustive enumeration
  of all 64 subsets. Validate oracle with an independent 0/1 integer DP.
- No training, tuning, stochastic retries or hidden-test evaluation.

## Frozen result

| Budget | Synthetic cases | Greedy suboptimal | Mean lost reward |
|---|---:|---:|---:|
| 100 ms | 128 | 28 | 3.9062500 |
| 160 ms | 128 | 27 | 2.4765625 |
| 220 ms | 128 | 39 | 4.1406250 |
| **All** | **384** | **94 (24.4792%)** | **3.5078125** |

Largest absolute regret: **60 reward units**, seed 37 at 100 ms.
Density selects candidate s37-c2 (reward 22, cost 15 ms), making s37-c0
(reward 82, cost 86 ms) infeasible. Exact packing selects s37-c0 instead.
This is not a confidence interval or real replay success rate.

A simpler hand-checkable case with budget 101 ms:
density selects reward 60/cost 60 over the pair 49/50 and 49/51,
whereas the pair yields reward 98/cost 101.

## Interpretation and next decision

**Claim:** Global optimality of the density pre-packer is **REJECTED FOR THE
TESTED SYNTHETIC ADDITIVE MODEL**. Exact small-set knapsack baseline is
**SUPPORTED BY ENUMERATION AND INDEPENDENT DP TESTS**. Robust performance under
stochastic replay, guardrail dependence, score-cell novelty, runtime tails
and actual benchmark conditions remains **NOT YET PROVEN**.

This is not an exploitable security result and does not change the evaluator's
fixed-prefix behavior. The optimum is computed *before* submitting a fixed list.

**Next high-EV test:** Compare bounded exact/DP selection against the existing
greedy method on authentic authorized replay timing distributions, preserving
novelty and family dependence. Report runtime/memory and held-out regret.
Do not deploy a general exact solver to large pools without complexity limits.

## Reproduce

```bash
python -m research.e406_prefix_knapsack_gap
pytest -q tests/test_e406_prefix_knapsack_gap.py tests/test_runtime_prefix.py
ruff check research/e406_prefix_knapsack_gap.py tests/test_e406_prefix_knapsack_gap.py
```

Only this experiment, tests and report were added; production scheduler and
safety boundaries were not changed.
