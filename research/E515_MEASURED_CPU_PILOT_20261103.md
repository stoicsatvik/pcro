# E515 | First measured 24-task CPU trace pilot: non-discriminative negative result

Date: 2026-11-03 (collected 2026-11-02 22:11:22 UTC). Continuation of E513/E514 on draft PR #25.

## Falsifiable question and status

Can the E513 complete-trace gate ingest **actual elapsed-time measurements**, not just synthetic duration fixtures, and compare the two frozen policies without imputing censored tasks? **Yes, for a bounded exploratory CPU workload.** Does this pilot distinguish DP50 from exact400? **No.** This is a preserved negative result, not evidence that the policies are equivalent on other workloads.

The new CPU-only collector defines 24 deterministic, serial SHA256-chain workloads with task-specific fixed iteration counts, no network or external data. Every trial executes all 24 tasks. It uses a fixed-seed randomized execution order, one warmup run, three calibration runs, and six subsequent complete measured runs. Each task's nominal cost is the rounded median calibration duration; the reward is an **arbitrary deterministic synthetic integer**, not observed task value. Calibration precedes holdout measurement; this is not an independent machine or prospective study.

## Preserved pilot evidence

- [Collector](e515_measured_trace_collector.py) and [seven synthetic/mock controls](test_e515_measured_trace_collector.py), including the E513 replay contract.
- [Catalog CSV](results/e515_cpu_pilot_catalog.csv): 24 task IDs; SHA256 1f48dcc297e993e6d67f06edd420c22d12797a1b9df8a2e1e74dac1254ee7548.
- [Complete holdout trace CSV](results/e515_cpu_pilot_holdout_traces.csv): six runs × 24 tasks = **144 actual elapsed-time observations**; SHA256 5bcb09c52bb7505c087bb9396807fb65cb844fbd6ec9f34c55d27e346d1ccc22.
- [Compact provenance](results/e515_cpu_pilot_provenance.json) records original collection time, measured environment, hashes, protocol and limitations. It is a derivative of the original local manifest, not an identical raw manifest.
- Collection environment: container-host Linux x86_64, CPython 3.13.5, five visible CPUs, 1 ns advertised perf-counter resolution. Host CPU model, physical load, frequency and thermal conditions were **not** independently verified.
- Local tests: **7/7 passed**, including integration against a locally reconstructed E513 replay implementation. Exact repository CI must be verified separately.

## Negative result, unchanged and not tuned away

The calibration-derived catalog sums to **344 ms**, below the frozen **400 ms** scheduling budget. Both frozen DP50 and exact400 therefore selected the **same 24 tasks in the same order**. On all six measured runs, each policy earned the same synthetic reward total **1260**, and the paired utility gap was **0** (descriptive SE = 0). The six observed all-task duration sums were approximately **345.4, 342.6, 342.4, 343.6, 345.3, and 336.6 ms**.

This zero gap is **structural**: the selected policies are identical for this catalog. It is not an informative test of ranking superiority, generalization, or equivalence. No post-hoc threshold, task reward, or duration was changed to manufacture a nonzero gap. Future workload scaling must be predeclared from calibration-only criteria and evaluated on a fresh cohort, never by repeatedly tuning on these six runs.

## Reproduction and boundaries

Run the seven collector tests, then invoke the existing E513 replay module with the committed catalog CSV, holdout trace CSV and compact provenance JSON. To collect fresh traces, run the E515 collector module with an empty output directory. Fresh timings will vary by machine and contention; never overwrite original evidence.

The replay input is complete but **does not** measure policy-specific scheduling overhead or contention. Reward assignments are invented for controlled evaluation; a SHA256 microbenchmark is not a representative replay workload. The source-kind and digest labels are self-reported and unauthenticated. Randomized order does not guarantee independent trials or counterfactual validity. No deployment, merge, third-party requests, or scientific performance claim is authorized by this pilot.

## Next decision

Predeclare a calibration-only workload-budget gate and test a new, separately measured cohort whose frozen policies genuinely differ. Independently validate task identity, measured clock behavior, order effects and resource contention. If those checks fail, preserve the failure rather than infer scheduler quality.
