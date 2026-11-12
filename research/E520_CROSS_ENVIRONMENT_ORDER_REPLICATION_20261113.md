# E520 — cross-environment replication of the E518/E519 run-order association

Date: 13 November 2026  
Branch: research/e520-cross-environment-order-replication-20261113  
Base: research/e519-run-order-sensitivity-20261112  
Pre-registration commit: 45245d6c24490b1839998aa230ac9e7050fcb501

## Question

Does the negative execution-position association found in E518/E519 recur under a new runtime profile when the exact E516 SHA256 workload and scaling are retained but task order is independently randomized?

## Frozen protocol

- 24 deterministic CPU tasks; exact E516 SHA256-chain workload definition.
- Per-task rounds are the E515 base schedule multiplied by 3/2 with integer half-up rounding; no tuning after measurement.
- One warmup, three calibration runs, six complete holdout runs.
- Independent order seed: 3844087846 (0xE5202026).
- The primary analysis is a two-way task/run fixed-effects slope of log duration against normalized within-run position.
- Secondary checks: 9,999 within-run position permutations (seed 3844087847), raw-duration scale, per-run slopes, leave-one-task-out, leave-one-run-out, first/last-position trimming, and task-rank stability.
- Every task output digest was deterministic across all ten runs.

## Observed result

| Metric | E519 original host cohort | E520 new runtime profile |
|---|---:|---:|
| Holdout observations | 144 | 144 |
| Log-duration slope per full run | -0.0523643 | **-0.0047538** |
| Within-run permutation reference p | 0.0066 | **0.8185** |
| Run-specific slopes | 5 negative / 1 positive | **4 negative / 2 positive** |

E520 details:
- First-to-last multiplicative ratio implied by the log slope: **0.99526**, about a 0.47% decrease over the full sequence.
- Partial R² after task and run effects: **0.00056**.
- 9,999-permutation null 2.5–97.5% interval: **−0.03656 to +0.03670**; the observed slope is unexceptional.
- Leave-one-task-out slopes cross zero: **−0.01853 to +0.00696**.
- First/last-position trimming slopes cross zero: **−0.03088 to +0.01293**.
- Raw-duration slope has the opposite sign: **+0.14989 ms per full run**.
- Pairwise task-rank stability is weak: median Spearman **−0.123**, range **−0.701 to +0.434**.
- Holdout run totals range from **520.79 to 577.80 ms**; no run was discarded.

## Environment and telemetry

- CPython 3.13.5, Linux kernel 6.18.57, x86_64.
- Runtime-reported CPU: AMD EPYC 9V74 80-Core Processor; three CPUs visible and affinity 0–2.
- /proc/cpuinfo reported 2596.138 MHz throughout. This is not dynamic frequency telemetry.
- Per-task UTC start timestamps, wall durations, and process CPU durations were recorded.
- Run-level /proc/stat counters and load averages were recorded. Load average was namespace/container-level and mostly zero.
- CPU scaling-frequency sysfs and thermal sensors were not exposed.

The E516 host profile recorded five visible CPUs but did not record CPU model or a host fingerprint. E520 is a **new execution-environment profile**, but independent physical-host identity is not authenticated. Do not label this a verified multi-host replication.

## Interpretation

The E519 negative run-order association does **not** transport cleanly to this new runtime profile. E520's primary slope is only 9.1% of the E519 magnitude, its permutation reference is non-small, its sensitivity checks cross zero, and the raw-duration outcome reverses sign.

This is a negative result against a broadly generalizable execution-position effect. It does not invalidate the original E519 same-host association; it indicates that the association is environment- or measurement-scale-dependent, or that the original effect was not stable across execution environments.

## Claim boundary

- E519 same-host order association: **SUPPORTED as a same-source candidate confound**.
- E520 order association in this runtime profile: **NOT DETECTED**.
- Cross-environment transportability: **NOT SUPPORTED by this single new profile**.
- Independent physical-host replication: **NOT MEASURED**.
- Causal mechanism: **NOT IDENTIFIED**.
- Real-task scheduler superiority: **NOT PROVEN**.

The workload is a SHA256 CPU microbenchmark with synthetic rewards, not a real PCRO replay workload. No policy superiority or deployment claim follows.

## Validation and artifacts

Local validation passed:
- 6 complete holdout runs × 24 unique tasks = 144/144 observations.
- Positive wall/process CPU durations, monotonic task positions, valid UTC timestamps.
- 24 stable task output digests across all ten runs.
- Trace/catalog/measurement/telemetry/analysis hashes checked.
- 9,999 permutation reference completed; leave-one-task and position-trimming checks completed.

No code changed and no GitHub Actions run or CI pass is claimed. The collection wrapper was executed in the analysis runtime using a source-equivalent implementation of the pinned E516 workload; the E516 collector source blob is pinned in provenance. The exact E520 measurement data, timestamps, run telemetry, pre-registration, and analysis receipt are preserved here.

## Next decisive gate

Collect on at least two independently identified physical hosts, with host fingerprints captured before measurement, independent randomized task orders, real CPU-frequency/load/temperature telemetry, and realistic executable tasks. Do not spend another run fitting more same-host flexibility to this SHA256 microbenchmark.
