import json
from pathlib import Path

import numpy as np
import pytest

from research.e518_run_order_confound import (
    AuditError,
    analyze,
    run,
)

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
TRACES = RESULTS / "e516_cpu_stress_holdout_traces.csv"
CATALOG = RESULTS / "e516_cpu_stress_catalog.csv"
PROVENANCE = RESULTS / "e516_cpu_stress_provenance.json"


def test_pinned_e516_trace_exposes_a_repeatable_negative_run_order_association():
    result = run(TRACES, CATALOG, PROVENANCE)
    assert result["cohort"] == {"runs": 6, "tasks_per_run": 24, "observations": 144}
    effect = result["run_order_effect"]
    assert effect["log_duration_slope_per_full_run"] == pytest.approx(-0.0523642835, abs=1e-8)
    assert effect["multiplicative_first_to_last"] == pytest.approx(0.9489831050, abs=1e-8)
    assert effect["permutation_p_two_sided"] == pytest.approx(0.0049, abs=1e-12)
    assert all(value < 0 for value in effect["leave_one_run_out_log_slopes"].values())
    assert result["task_rank_stability"]["median_pairwise_spearman"] > 0.99
    assert result["claim_boundary"]["causal_mechanism"] == "NOT IDENTIFIED"


def test_analyze_rejects_unbalanced_cohort_shape():
    with pytest.raises(AuditError):
        analyze(np.ones((5, 24)), np.tile(np.linspace(0, 1, 24), (5, 1)))


def test_analyze_detects_injected_order_drift_with_fixed_task_and_run_effects():
    rng = np.random.default_rng(518)
    n_runs, n_tasks = 6, 24
    positions = np.vstack([rng.permutation(np.linspace(0, 1, n_tasks)) for _ in range(n_runs)])
    task_cost = np.linspace(5, 40, n_tasks)
    run_scale = np.asarray([0.98, 1.01, 1.03, 0.99, 1.02, 1.00])[:, None]
    durations = task_cost[None, :] * run_scale * np.exp(-0.12 * positions)
    result = analyze(durations, positions, n_permutations=1999, seed=518)
    assert result["run_order_effect"]["log_duration_slope_per_full_run"] < -0.10
    assert result["run_order_effect"]["permutation_p_two_sided"] < 0.01


def test_pinned_receipt_is_deterministic():
    first = run(TRACES, CATALOG, PROVENANCE)
    second = run(TRACES, CATALOG, PROVENANCE)
    assert first["run_order_effect"] == second["run_order_effect"]
    assert first["variance_decomposition_r2"] == second["variance_decomposition_r2"]


def test_trace_digest_tampering_is_rejected(tmp_path):
    trace_copy = tmp_path / "traces.csv"
    trace_copy.write_bytes(TRACES.read_bytes() + b"\n")
    with pytest.raises(AuditError, match="trace digest mismatch"):
        run(trace_copy, CATALOG, PROVENANCE)


def test_incomplete_run_is_rejected_even_with_updated_self_reported_digest(tmp_path):
    import hashlib

    raw = TRACES.read_bytes()
    lines = raw.decode().splitlines()
    tampered = "\n".join(lines[:-1]) + "\n"
    trace_copy = tmp_path / "traces.csv"
    trace_copy.write_text(tampered, encoding="utf-8")
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    provenance["trace_sha256"] = hashlib.sha256(trace_copy.read_bytes()).hexdigest()
    provenance_copy = tmp_path / "provenance.json"
    provenance_copy.write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(AuditError, match="every E516 run must contain all 24 tasks"):
        run(trace_copy, CATALOG, provenance_copy)
