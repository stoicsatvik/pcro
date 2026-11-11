# E519 — same-source sensitivity of the E518 run-order association (12 November 2026)

## Question

Does the E518 negative execution-position association depend on one task, the first few executions, the last few executions, or the log-duration outcome scale?

This is a sensitivity pass on the same frozen 144 observations. It is not a new collection or independent replication.

## Frozen source

- Dataset: E516_CPU_SHA256_FRESH_STRESS
- Six runs × 24 tasks = 144 observations.
- Trace SHA-256: e00881175d3294a5f03a1cce090015047e955847955e195142403249f975ff7d.
- Catalog SHA-256: e68d92ce969f30b2dc80b4c688071c57f15350b05c6aa992d53ed97db81557b6.
- The existing E518 validator checks source hashes, six-run ordering, the complete 6×24 panel, task catalog and positive finite durations before this analysis runs.

## Experiments

1. Reproduce the two-way fixed-effects log-duration slope.
2. Refit after deleting each task ID in turn (24 leave-one-task-out fits).
3. Refit after removing the first 1–5 or last 1–5 execution positions within every run, retaining task and run fixed effects in the resulting unbalanced panel.
4. Run an exploratory within-task rank sensitivity with 9,999 within-run position permutations (seed 20261112).
5. Preserve each run-specific slope rather than treating six runs from one host as six independent machines.

The rank permutation and trimming analyses are same-source robustness diagnostics. Their permutation fractions are not probabilities of a physical mechanism.

## Results

- Reproduced E518 log-duration slope: **−0.0523643** per full execution sequence.
- New 9,999-draw within-run permutation reference (seed 20261112): **p = 0.0066** for the log-duration slope.
- All **24/24 leave-one-task-out** slopes remain negative; range **−0.0628175 to −0.0458899**.
- All **10/10 position-trimming** slopes remain negative; range **−0.0936237 to −0.0617475**.
  - Removing the first 1–5 positions makes the fitted slope more negative, not weaker.
  - Removing the last 1–5 positions leaves a similar negative slope.
- Exploratory within-task rank slope: **−1.7026 rank units per full run**, with same-data permutation reference **p = 0.0004**.
- Run-specific task-adjusted slopes: five negative and one positive. The positive run is holdout-002 (+0.0180); holdout-003 is notably more negative (−0.1743). This heterogeneity is retained rather than averaged away.

## Interpretation

The E518 association is **robust to deleting any one task and to trimming up to five early or late positions** in this pinned dataset. The effect is not explained solely by a single task or by the first/last few executions.

However, run-specific slopes are heterogeneous, and all six runs share one container host. The result therefore supports a **same-host order/warmup/runtime-state confound candidate**, not a general execution-order law. Plausible mechanisms remain warmup/cache effects, CPU frequency changes, thermal behavior, process state or time-varying contention. The data contain no timestamps, CPU-frequency, temperature, utilization or host-level telemetry to discriminate among them.

## Claim boundary

- Robust same-source order association: **SUPPORTED**.
- Causal mechanism: **NOT IDENTIFIED**.
- Independent-host replication: **NOT MEASURED**.
- Real-task scheduler effect or policy superiority: **NOT PROVEN**.
- This is not new evidence independent of E516/E518 and does not authenticate the self-reported measurement provenance.

## Validation

A source-equivalent local analysis in this run reproduced the E518 slope and the sensitivity ranges above. The dedicated GitHub Actions workflow on this exact branch will rerun deterministic source/integrity tests, sensitivity tests and a compact receipt; its exact-head result is pending until Actions completes.

## Next decisive gate

Collect a fresh cohort on multiple independently identified hosts with independently randomized task order, per-task timestamps, CPU frequency/load/temperature telemetry, controlled warmups and host-level holdout. Do not add further same-host polynomial/model flexibility as a substitute for that measurement.
