# E514 | Bind paired replay to exact task-catalog bytes

Date: 2026-11-03. Continuation of E513 on draft PR #25. **No measured traces acquired or claimed.**

## Falsifiable failure mode

E513 verified the raw trace CSV digest, but not the catalog CSV. An operator could change a task's reward or nominal duration, leave the trace CSV and its SHA256 unchanged, and still pass the previous provenance gate. Since the frozen `policies(rows)` and `realized(rows, ...)` both depend on catalog rewards/durations, the same trace could be interpreted under a different task contract. The previous schema permitted this because it checked only `trace_sha256`.

**Hypothesis:** binding the exact catalog bytes to the provenance record will reject catalog-only rewrites without altering the frozen DP50/exact400 policy algorithms or trace replay semantics.

## Narrow engineering change

- Require `catalog_sha256` alongside `trace_sha256` in provenance JSON for **both** synthetic and measured sources. Both are hashes of the original raw file bytes, not normalized CSV values.
- Change `check_provenance(path, trace_path, catalog_path)` to verify both digests before `evaluate()` parses or scores the catalog. The new required third argument intentionally breaks the old two-argument research helper API.
- Return the catalog digest in the result JSON so a report can identify the exact input contract. Keep the E513 24-task, two-complete-run, units and descriptive-SE gates unchanged.
- Existing E513 test fixtures now supply both digests; three new tests cover catalog-only tampering, a missing catalog digest and a **negative control** in which both the catalog and its metadata are rewritten consistently.

## Predeclared test interpretation

1. Mutate a valid task reward while keeping trace bytes and provenance fixed. **Expected:** reject with `catalog SHA256 mismatch`.
2. Remove the catalog digest. **Expected:** reject, not silently accept a legacy manifest.
3. Rewrite both catalog and provenance together. **Expected negative control:** still accepted. A mutable manifest and catalog cannot authenticate one another.

Commands:

```bash
python -m unittest discover -s research -p 'test_e513_trace_replay.py' -v
python -m research.e513_trace_replay catalog.csv complete_runs.csv provenance.json
```

The output is a **contract-bound replay calculation**, not proof of actual execution, measurement origin, stationarity, independence, task semantics, or causal scheduling benefit. SHA256 only detects accidental or adversarial *inconsistent* edits relative to the self-reported manifest. An attacker who can edit both files can forge consistent hashes. Catalog bytes do not define a runnable workload or a trusted task identity.

## Decision

Do not claim empirical policy superiority. Next acquire complete measured traces for independently specified 24 executable tasks, bind an externally reviewable task definition and collection protocol, record environment and order, and predeclare inclusion/holdout before computing utility. Keep draft and unmerged; no new outreach justified by a schema hardening test alone.

## Validation record

CI outcomes are recorded in the PR discussion once the exact-head workflow finishes. No physical latency measurements or external benchmarks are bundled.
