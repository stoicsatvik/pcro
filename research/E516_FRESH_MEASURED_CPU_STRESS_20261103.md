# E516 | Fresh measured CPU stress after E515's non-discriminative pilot

Date: 2026-11-03 (collected 2026-11-02 23:10:32 UTC). Continuation of draft PR #25.

## Predeclared hypothesis and protocol

E515 measured six complete runs, but both frozen policies selected all 24 tasks because the nominal total was 344 ms against a 400 ms budget. That zero gap was non-discriminative. Before observing any E516 timing, fix the SHA256 workload to **3/2 times the E515 per-task iteration counts**, using exact integer rounding. This is a design choice informed by the E515 pilot, **not** a statistically independent preregistration. Keep the same 24 task IDs, arbitrary rewards, 400 ms budget, 50-unit miss penalty, and frozen DP50/exact400 implementations.

Collect one randomized warmup, three complete randomized calibration runs, freeze nominal task costs from the rounded calibration medians, calculate both selected task sequences **before** holdout, and then collect six new complete randomized holdout runs. No post-hoc scale, budget, task reward, or policy tuning is permitted. A divergent pre-holdout selection is a necessary but not sufficient condition for an informative paired replay. The predeclared descriptive endpoint is mean paired utility DP50 minus exact400 with the existing E513 scoring and descriptive standard error; no superiority threshold or confirmatory p-value is claimed.

## Observed result and preserved negative evidence

The fresh calibration catalog totaled **526 ms**, and the pre-holdout gate found **22 tasks for DP50** versus **19 for exact400**. Both policies shared their first 19 task IDs; DP50 attempted three additional tasks. The policies therefore differ structurally on this fresh catalog, unlike E515.

| Run | DP50 utility | exact400 utility | Paired gap |
|---|---:|---:|---:|
| holdout-000 | 1076 | 1076 | 0 |
| holdout-001 | 1122 | 1172 | -50 |
| holdout-002 | 1122 | 1172 | -50 |
| holdout-003 | 1076 | 1076 | 0 |
| holdout-004 | 1122 | 1172 | -50 |
| holdout-005 | 1122 | 1172 | -50 |

**Mean paired gap: -33.333 synthetic utility units; descriptive SE: 10.541.** On four runs, DP50 encountered a missed-task penalty after the shared prefix while exact400 stopped; on two runs both scores were equal. This is a *negative* result for DP50 on this small measured CPU cohort. It is not evidence of general scheduler superiority for exact400.

Complete measured duration sums across the six runs were **533.579, 527.499, 523.989, 561.516, 514.748, 502.535 ms**. The unusual 561.516 ms run illustrates uncontrolled timing variability; do not remove it. The 144 holdout observations and exact 24-task catalog are preserved in the results directory. The compact provenance is explicitly a derivative of the original collection-time manifest; raw run-order and per-task output-digest logs were not committed.

Trace SHA256: e00881175d3294a5f03a1cce090015047e955847955e195142403249f975ff7d.
Catalog SHA256: e68d92ce969f30b2dc80b4c688071c57f15350b05c6aa992d53ed97db81557b6.
Measurement-time collector source SHA256: b56678c70a26ead594a47779c0d01cbd7b6c541bd3d8d9e124b1155c79df526e.

Collection environment: container-host Linux x86_64, CPython 3.13.5, five visible CPUs, 1 ns advertised perf-counter resolution. No independently verified CPU frequency, load, thermal state or isolation. These are wall-clock observations of a SHA256 microbenchmark, not real production task traces.

## Validation and limitations

Seven new synthetic/mock collector and calibration-gate controls passed locally. The original E513 replay contract must also pass on exact committed bytes in GitHub CI; record that status separately, not as an assumed success. All E515 evidence remains unchanged.

The 3/2 multiplier was selected using the earlier exploratory pilot and cannot support independent confirmation. Six sequential runs from one host are not independent machines; randomized order does not establish independent trials. Arbitrary rewards and a fixed missed-task penalty are modeling assumptions. The replay omits policy overhead and contention, and self-reported hashes are not trusted provenance. Do not generalize this synthetic-utility ranking to real workloads, and do not contact external experts claiming scheduler superiority. Next gate: independently collected traces from realistic executable tasks on multiple machines, frozen workload definitions and a prospective inclusion plan.
