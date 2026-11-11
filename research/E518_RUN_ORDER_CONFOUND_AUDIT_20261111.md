# E518 — execution-order confound audit of E516 measured CPU traces (2026-11-11)

## Question

Do the six complete E516 holdout runs behave as exchangeable task-duration observations, or does measured duration drift systematically with execution position after controlling for task identity and run-wide level?

This is a diagnostic reanalysis of the existing E516 measurements. It is not a new collection, independent replication, or real-workload benchmark.

## Frozen source and integrity

- Source branch: `research/e507-matched-copula-family-20261102`
- Dataset: `E516_CPU_SHA256_FRESH_STRESS`
- Trace: six runs × 24 tasks = **144 measured elapsed-time observations**.
- Trace SHA-256: `e00881175d3294a5f03a1cce090015047e955847955e195142403249f975ff7d`.
- Catalog SHA-256: `e68d92ce969f30b2dc80b4c688071c57f15350b05c6aa992d53ed97db81557b6`.
- Provenance declares `source_kind=measured`, but that label and the adjacent hashes are self-reported, not independently authenticated.
- E516 collector appends rows in the actual randomized execution order. E518 uses that CSV row order as normalized position within each run; it does not reconstruct or invent timestamps.

## Frozen analysis

Model:

`log(duration_ms) = task fixed effects + run fixed effects + beta × normalized execution position + residual`

- The 6×24 panel is complete and balanced.
- The order coefficient is tested with **9,999 within-run permutations** of execution positions, preserving each run's position set and the measured duration/task values.
- Two-sided finite-sample permutation p-value uses `(1 + exceedances)/(B + 1)`.
- The task and run effects are additive on log duration. The permutation test assumes randomized task order under the no-order-effect null.
- No policy, budget, reward, duration, or task is retuned.

## Result

<badge>Candidate confound detected</badge>

| Metric | Result |
|---|---:|
| Observations | 144 |
| Full-run log-duration slope | -0.0535019 |
| First-to-last multiplicative duration ratio | 0.947904 |
| Partial R² for order after task + run effects | 0.069529 |
| Two-sided within-run permutation p | 0.0042 |
| Median pairwise task-duration rank Spearman | 0.995652 |
| Task-only R² | 0.986739 |
| Run-only R² | 0.002982 |
| Task + run R² | 0.989721 |
| Task + run + order R² | 0.990436 |

The fitted position effect corresponds to approximately **5.21% lower duration from the first to last execution position**, conditional on task and run fixed effects. Five of six run-specific slopes are negative; all six leave-one-run-out estimates remain negative (range approximately -0.0236 to -0.0659 log units per full run).

Task identity still dominates the measured cost structure: median pairwise task-rank correlation is approximately 0.996, and task-only R² is 0.987. But the order association is not negligible relative to the remaining variation.

## Interpretation

This is evidence that the E516 single-host microbenchmark's task durations are **not exchangeable across execution position** under the tested model. It weakens the assumption that a fixed task-duration table can be replayed independently of schedule order. It may affect counterfactual comparisons between policies that execute different prefixes or orders.

The mechanism is **not identified**. Plausible explanations include warmup/cache effects, CPU frequency ramping, process/runtime state, thermal behavior, or time-varying host contention. E516 contains no timestamps, CPU-frequency telemetry, temperature, load telemetry, or independent host replication to distinguish them.

This does not establish a real production scheduler effect, policy overhead, causal superiority, or a general latency law. E516's tasks are SHA256 CPU microbenchmarks and its rewards are arbitrary synthetic integers. The 3/2 workload multiplier was selected after the E515 pilot, so E516 is not independent of that design choice.

## Preserved failures and boundaries

- E515's zero policy gap remains structural because both frozen policies selected all 24 tasks.
- E516's negative DP50-minus-exact400 mean and its single-run 561.516 ms high total remain unchanged.
- E517's post-hoc budget sign reversal remains a same-data sensitivity diagnostic, not independent evidence.
- E518 does not alter E516 traces, catalog, provenance or policy scores.
- No real task utility, multiple-machine evidence, scheduler overhead, or causal counterfactual is claimed.

## Next discriminating experiment

Collect a fresh, multi-host cohort with task execution order randomized independently per run, explicit per-task timestamps, CPU frequency/load/temperature telemetry, controlled warmups, and repeated blocks. Predeclare a block/order model and host-level split before collecting. Compare:
1. unadjusted duration tables;
2. task + host/run fixed effects;
3. order-adjusted durations;
4. within-block randomized order;
5. fresh policy replay with measured scheduler overhead.

If order drift disappears under randomized blocked acquisition, the current effect is likely host/runtime-state-specific. If it persists across hosts and blocks, it becomes a stronger scheduling confound candidate. Do not call the current six-run result an independent replication.
