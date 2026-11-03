"""E517: post-hoc budget sensitivity of frozen E516 measured-trace replay.

Diagnostic only: the 400 ms policy selections and six E516 observations stay fixed.
Changing the replay budget is NOT a prospective policy evaluation.
"""
import argparse
import json
from pathlib import Path

from research.e507_gaussian_copula import BUDGET, PENALTY
from research.e513_trace_replay import (
    check_provenance,
    evaluate,
    load_catalog,
    load_complete_runs,
)

MIN_BUDGET_MS = 350
MAX_BUDGET_MS = 500


def replay_at_budget(rows, selected, durations, budget_ms, penalty=PENALTY):
    """Match frozen realized() semantics, changing only the replay budget."""
    if type(budget_ms) is not int or budget_ms < 1:
        raise ValueError("budget_ms must be a positive integer")
    if type(penalty) is not int or penalty < 0:
        raise ValueError("penalty must be a nonnegative integer")
    elapsed = 0.0
    reward = 0
    for task_id in selected:
        _, task_reward, _ = rows[task_id]
        if elapsed + durations[task_id] > budget_ms:
            return reward - penalty
        elapsed += durations[task_id]
        reward += task_reward
    return reward


def sweep(catalog_path, trace_path, provenance_path):
    """One prespecified inclusive integer grid, no tuning or dropped runs."""
    meta, _ = check_provenance(provenance_path, trace_path, catalog_path)
    if meta["dataset_id"] != "E516_CPU_SHA256_FRESH_STRESS" or meta["source_kind"] != "measured":
        raise ValueError("E517 is restricted to the frozen E516 measured cohort")
    baseline = evaluate(catalog_path, trace_path, provenance_path)
    rows = load_catalog(catalog_path)
    runs = load_complete_runs(trace_path)
    selected = baseline["policies"]
    gate = meta.get("pre_holdout_gate")
    expected_gate = {
        "dp50": selected["dp50"],
        "exact400": selected["exact400"],
        "divergent": selected["dp50"] != selected["exact400"],
        "nominal_total_ms": sum(row[2] for row in rows),
    }
    if gate != expected_gate:
        raise ValueError("provenance policy gate disagrees with frozen catalog")
    if BUDGET != 400 or PENALTY != 50:
        raise ValueError("frozen scoring contract changed")
    points = []
    for budget in range(MIN_BUDGET_MS, MAX_BUDGET_MS + 1):
        gaps = [
            replay_at_budget(rows, selected["dp50"], durations, budget)
            - replay_at_budget(rows, selected["exact400"], durations, budget)
            for durations in runs.values()
        ]
        points.append({"budget_ms": budget, "mean_gap": sum(gaps) / len(gaps), "gaps": gaps})
    baseline_gaps = [item["gap"] for item in baseline["per_run"]]
    at_400 = points[BUDGET - MIN_BUDGET_MS]
    if at_400["gaps"] != baseline_gaps:
        raise AssertionError("E517 replay disagrees with E513 at frozen 400 ms")
    positive = [point["budget_ms"] for point in points if point["mean_gap"] > 0]
    negative = [point["budget_ms"] for point in points if point["mean_gap"] < 0]
    return {
        "experiment": "E517_POSTHOC_FROZEN_POLICY_BUDGET_SENSITIVITY",
        "dataset_id": meta["dataset_id"],
        "trace_sha256": meta["trace_sha256"],
        "catalog_sha256": meta["catalog_sha256"],
        "source_kind": meta["source_kind"],
        "run_count": len(runs),
        "frozen_policy_budget_ms": BUDGET,
        "miss_penalty": PENALTY,
        "sweep_range_ms": [MIN_BUDGET_MS, MAX_BUDGET_MS],
        "mean_gap_at_400": at_400["mean_gap"],
        "mean_gap_at_450": points[450 - MIN_BUDGET_MS]["mean_gap"],
        "first_positive_budget_ms": min(positive) if positive else None,
        "negative_budget_count": len(negative),
        "positive_budget_count": len(positive),
        "zero_budget_count": len(points) - len(positive) - len(negative),
        "points": points,
        "limitations": (
            "Post-hoc diagnostic on the same six E516 runs. Only replay budget changes; "
            "both policies remain selected using the original 400 ms calibration catalog. "
            "Budget choices are not new independent experiments. Self-reported measurement "
            "provenance, arbitrary rewards, unmeasured overhead and host effects remain unresolved."
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E517 E516 post-hoc budget sensitivity")
    parser.add_argument("catalog", type=Path)
    parser.add_argument("traces", type=Path)
    parser.add_argument("provenance", type=Path)
    args = parser.parse_args()
    print(json.dumps(sweep(args.catalog, args.traces, args.provenance), indent=2))
