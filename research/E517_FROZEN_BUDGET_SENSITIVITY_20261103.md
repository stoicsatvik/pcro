# E517 | Post-hoc budget sensitivity of E516 frozen policies

Date: 2026-11-03. Continuation of draft PR #25. This is a **diagnostic reanalysis of the same six E516 holdout runs**, not a fresh cohort or a new preregistered confirmation.

## Falsifiable question and frozen contract

E516 found mean DP50-minus-exact400 synthetic utility **-33.333** at the original **400 ms** budget. Does that sign remain invariant to the replay deadline when both policy selections, all 24 task rewards, all 144 measured durations, and the 50-unit miss penalty stay fixed?

Before inspecting the sweep, define the inclusive integer replay-budget grid **350..500 ms** in 1 ms steps. Never re-optimize policies when changing the replay budget: the E516 catalog's calibration-only 400 ms choices remain DP50 (22 tasks) and exact400 (19 tasks). Keep the original E516 trace and catalog bytes and hashes unchanged. This sensitivity question is post-hoc and cannot validate an optimal budget or causal performance.

## Results and negative evidence

| Replay deadline | Six paired DP50-minus-exact400 gaps | Mean gap |
|---|---|---:|
| 400 ms (original) | 0, -50, -50, 0, -50, -50 | **-33.333** |
| 448 ms | -19, -19, -3, -19, -3, +55 | -1.333 |
| 449 ms | -19, -3, -3, -19, -3, +55 | **+1.333** |
| 450 ms | -19, -3, -3, -19, -3, +55 | **+1.333** |
| 480 ms | +55, +55, +55, +55, +55, +55 | **+55** |

Across all **151** integer budget settings: **74 negative**, **25 zero**, **52 positive** mean gaps. The first positive mean occurs at **449 ms**, which is a *post-hoc threshold found by scanning the same observations*, not a newly established operating point. The 400 ms negative ranking is therefore **not robust to a ~12.25% deadline relaxation** on this particular cohort. The opposite positive ranking at 449/450 ms is **equally non-generalizable**.

At 400 ms, two runs fail at the shared 19th task, so both policies incur the same penalty. In the other four runs, exact400 completes 19 tasks while DP50 attempts an extra task and incurs the 50-unit penalty. At 450 ms, the extra attempts sometimes earn reward and sometimes incur penalties; the mean sign changes. The exact sign is a discontinuous function of cumulative durations and the fixed 50-unit penalty.

## Validation and interpretation

`research/e517_budget_sensitivity.py` loads the original E516 CSVs through the E513 strict provenance and complete-run gate, recomputes the 400 ms policy choices, checks the stored calibration-only policy gate, and asserts exact agreement with E513's original per-run 400 ms scores before producing the grid. Five deterministic regression tests cover strict deadline boundary, penalty semantics, invalid parameters, exact E516 replay/sign reversal, tampered gate, and source-kind rejection (the invalid-parameter cases share a test). No new data are collected or overwritten.

**Limitations:** E516 uses six sequential complete CPU microbenchmark runs on one container host; the tasks' rewards and missed-task penalty are synthetic. The 3/2 workload scale was chosen after E515. This reanalysis has no new independent holdout, no measured scheduler overhead or real task utilities, no machine diversity, and no authenticated provenance. The 449 ms threshold is a descriptive sensitivity breakpoint, not an optimization recommendation or an empirical superiority claim. Reusing the same six runs at 151 deadlines is not 151 independent experiments.

**Next gate:** Freeze a representative workload, reward/penalty contract, operational deadline and host-quality criteria **before** collecting new independent traces from multiple machines. Do not select a budget based on E517's sign flip and then describe the next test as independent without declaring that design choice.
