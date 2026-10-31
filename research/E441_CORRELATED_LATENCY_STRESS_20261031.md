# E441 | Correlated synthetic latency changes the nominal-exact/greedy ordering

Date: 2026-10-31. **Scope:** synthetic additive abstract scheduling only. No actual evaluator replay, security payloads, guardrail bypass, platform submission or production change.

## Question and frozen design

E426 showed nominal exact knapsack has **lower realized fixed-prefix reward** than density greedy under independent bounded latency noise. Does this ordering persist when every candidate in a replay batch experiences a shared latency shock?

Reuse E426's **128 seeds (128–255), 24 candidate costs/rewards, 400 ms budget, 64 deterministic draws per seed**, and four unmodified pre-replay selectors: density greedy/exact DP at 400 ms and 340 ms nominal caps. Every candidate list is fixed **before** noise is sampled. The evaluator stops at the first item exceeding 400 ms, never skipping it. Compare three analyst-defined noise families:

1. **Independent:** unchanged E426 per-candidate multiplier in [0.7,1.3).
2. **Half-shared:** 50% independent plus 50% separately salted common multiplier. This changes *both* dependence and marginal variance, so is not a clean correlation-only intervention.
3. **Fully shared:** one separately salted uniform [0.7,1.3) multiplier for every candidate, preserving the one-dimensional marginal distribution while introducing perfect within-draw dependence.

These are hypothetical distributions, not measured latency. The same 128 seeds are reused, so E441 is **sensitivity analysis**, not a new independent holdout.

## Actual results (8,192 paired draws per noise family)

| Noise family | Greedy 400 realized | Exact 400 realized | Exact − greedy | Greedy truncation | Exact truncation |
|---|---:|---:|---:|---:|---:|
| Independent | 642.452271 | 639.470703 | **−2.981567** | 30.8716% | 40.3320% |
| Half-shared | 636.444092 | 634.793335 | **−1.650757** | 38.2446% | 44.8486% |
| Fully shared | 623.540039 | 624.395142 | **+0.855103** | 44.5923% | 48.0347% |

Paired seed wins/losses/ties for nominal exact versus greedy: independent **17/48/63**, half-shared **24/41/63**, fully shared **39/26/63**. These are 128 paired *seed-level* comparisons, not 8,192 independent statistical units. No p-value or empirical superiority claim is made.

The 340 ms cap lowers truncation at the cost of substantial mean reward. Under fully shared noise, greedy/exact 340 ms cap mean realized rewards are **591.435669 / 592.850342** and truncation rates **13.2690% / 16.6504%**. Under independent noise the corresponding means are **598.205566 / 603.623779** and truncation **0.0732% / 0.1953%**.

## Validation

- Reconstructed **byte-identical Git blobs** of E406, E426, production PCRO runtime, and their committed tests. Git blob SHA-1s matched GitHub.
- Executed **nine previously unexecuted exact-source E406/E426 pytest tests** successfully.
- Added E441 source and tests; **13/13 local pytest tests passed** across E406, E426, E441. Both E441 Git blobs matched the locally executed files byte-for-byte.
- Independently authored Node.js scheduler, integer knapsack, noise generator and fixed-prefix simulator agreed **exactly** on all three noise-family receipts and paired seed counts.
- **Full inherited repository suite, Ruff, and exact-final-head GitHub Actions NOT RUN.** Prior included Actions minutes were reportedly exhausted. No paid CI requested.

## Interpretation and next gate

**REJECTED FOR THESE SYNTHETIC FAMILIES:** a fixed nominal exact-versus-density ordering is invariant to the latency dependence model. The observed sign reverses between independent and fully shared noise. This is a sensitivity result, **not evidence that nominal exact is superior in real replay**. There is no real replay latency, success probability, reward dependence, or empirical scheduler calibration.

**NOT YET PROVEN:** robust chance-constrained scheduling, real-world latency tail behavior, evaluator reward, security outcomes or transfer.

**Highest-EV next:** obtain legitimately authorized replay timing traces with provenance, freeze independent candidate/timing holdouts, estimate within-batch latency dependence and tail calibration, then compare density, exact and chance-constrained policies with paired seed and batch units. Include score-cell dependence and measured runtime overhead. Do not change production policy on this synthetic evidence.

## Reproduce

    python -m research.e441_correlated_latency_stress
    python -m pytest -q tests/test_e406_prefix_knapsack_gap.py tests/test_e426_latency_uncertainty.py tests/test_e441_correlated_latency_stress.py
