# E513 | Complete paired trace-replay gate

Date: 2026-11-03. Continuation of E512 on draft PR #25. **No real latency data acquired or claimed.**

## Why this gate exists

E511's completion-only proxy and E512's reward-prefix proxy failed predeclared cross-family tests. Further synthetic proxy tuning risks fitting assumptions rather than measuring scheduling behavior. Before evaluating actual latency traces, require a data path that **rejects incomplete or policy-censored task runs**. A trace recorded only until a scheduler stops cannot estimate the counterfactual utility of a different schedule without additional assumptions.

## Frozen input contract

- Catalog CSV header: `task_id,reward,nominal_ms`. Exactly 24 task IDs `0..23`, unique, positive integer rewards and nominal durations. This preserves the E507 fixture shape and frozen budget (400 ms), missed-task penalty (50), and policy constructors.
- Trace CSV header: `run_id,task_id,duration_ms`. At least two run IDs; every run must contain all 24 tasks exactly once. Durations must be finite and strictly positive. No missing values, extra columns, duplicates or policy-truncated runs.
- Provenance JSON requires `dataset_id`, `source_kind` (`measured` or `synthetic`), `time_unit: "ms"`, and `trace_sha256` of the **exact raw trace bytes**. Measured-labelled input also requires a nonempty `collection_protocol`. These are *self-reported labels*, not authenticated provenance.
- Reuse the E507 `policies()` and `realized()` functions without refitting. Each complete run is replayed through both frozen DP50 and exact400 policies, using each observed duration divided by that task's nominal duration. Report paired per-run utility gaps, their mean and descriptive standard error. No new correlation assumptions are introduced.

## Validation and falsification

The ten synthetic unit controls exercise replay parity against `realized()`, missing task/censoring, duplicates, nonfinite and nonpositive durations, digest tampering, required measured-source protocol, units, catalog IDs, extra columns and single-run standard-error rejection.

```bash
python -m unittest discover -s research -p 'test_e513_trace_replay.py' -v
python -m research.e513_trace_replay catalog.csv complete_runs.csv provenance.json
```

**No bundled trace is an empirical measurement.** Passing the gate establishes only that a dataset satisfies the declared schema and byte-level integrity check. A SHA256 recorded alongside a mutable dataset does not authenticate its origin; `source_kind: "measured"` is an assertion by its submitter. Full paired task runs are necessary for this replay but insufficient to guarantee independent trials, unchanged execution conditions, stationary task latency, no measurement overhead, or valid causal counterfactuals. In particular, running every task can itself alter contention relative to a policy that would have stopped.

## Next research decision

Acquire consented, reproducible, timestamped latency measurements for the **same 24 defined tasks** with documented hardware, load, execution order, warmup, trial boundaries and clock resolution. Keep raw files immutable and record independent source provenance. Freeze dataset inclusion and train/holdout splits before policy comparison. If complete counterfactual traces cannot be collected, **report that limitation** rather than silently filling missing durations or promoting synthetic scores to empirical evidence.

## Observed validation and preserved failure

- Initial E513 trace-gate workflow [#41516562509](https://github.com/stoicsatvik/pcro/actions/runs/41516562509) passed all **10 synthetic controls**.
- Initial full CI [#41516562554](https://github.com/stoicsatvik/pcro/actions/runs/41516562554) **failed Ruff**, specifically TRY004 (non-object provenance should raise TypeError) and I001 (test import formatting). Both issues were fixed in follow-up commits; the failure is retained here rather than erased.
- After corrections, exact-head E513 workflow [#41516803851](https://github.com/stoicsatvik/pcro/actions/runs/41516803851) passed. Full CI [#41516804251](https://github.com/stoicsatvik/pcro/actions/runs/41516804251) passed Ruff, pytest and 500 property seeds in its test job; JED parity was still in progress at this report update.

**No measured traces were supplied or evaluated.** This is a validated ingestion/replay interface, not a real-world scheduling result.
