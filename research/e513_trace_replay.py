"""E513: fail-closed, provenance-labelled trace replay gate.

Requires complete paired 24-task runs, not censored logs from a policy that
stops early. This module does not acquire or authenticate measured traces.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

from research.e507_gaussian_copula import PENALTY, fixture, policies, realized

CATALOG_COLUMNS = ["task_id", "reward", "nominal_ms"]
TRACE_COLUMNS = ["run_id", "task_id", "duration_ms"]
N_TASKS = len(fixture(0))


def _rows(path, expected):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != expected:
            raise ValueError(f"CSV columns must be exactly {expected}")
        rows = list(reader)
    if not rows or any(None in row or any(v is None or not v.strip() for v in row.values()) for row in rows):
        raise ValueError("CSV has empty, missing or extra fields")
    return rows


def _integer(value, name, minimum):
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {name}") from exc
    if str(result) != value.strip() or result < minimum:
        raise ValueError(f"invalid {name}")
    return result


def _positive_finite(value, name):
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {name}") from exc
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"invalid {name}")
    return result


def load_catalog(path):
    rows = {}
    for entry in _rows(path, CATALOG_COLUMNS):
        task_id = _integer(entry["task_id"], "task_id", 0)
        if task_id in rows:
            raise ValueError("duplicate catalog task_id")
        reward = _integer(entry["reward"], "reward", 1)
        nominal = _integer(entry["nominal_ms"], "nominal_ms", 1)
        rows[task_id] = (task_id, reward, nominal)
    if set(rows) != set(range(N_TASKS)):
        raise ValueError("catalog must have exactly 24 consecutive task IDs 0..23")
    return [rows[i] for i in range(N_TASKS)]


def load_complete_runs(path):
    runs = {}
    for entry in _rows(path, TRACE_COLUMNS):
        run_id = entry["run_id"].strip()
        task_id = _integer(entry["task_id"], "task_id", 0)
        duration = _positive_finite(entry["duration_ms"], "duration_ms")
        if task_id >= N_TASKS:
            raise ValueError("out-of-range task_id")
        run = runs.setdefault(run_id, {})
        if task_id in run:
            raise ValueError("duplicate task measurement in a run")
        run[task_id] = duration
    if len(runs) < 2:
        raise ValueError("at least two complete runs required for descriptive SE")
    if any(set(run) != set(range(N_TASKS)) for run in runs.values()):
        raise ValueError("incomplete or policy-censored run; cannot compare counterfactual policies")
    return {key: [runs[key][i] for i in range(N_TASKS)] for key in sorted(runs)}


def check_provenance(path, trace_path):
    meta = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(meta, dict):
        raise TypeError("provenance must be a JSON object")
    if meta.get("time_unit") != "ms":
        raise ValueError("time_unit must be ms")
    if meta.get("source_kind") not in ("synthetic", "measured"):
        raise ValueError("source_kind must be synthetic or measured")
    if not isinstance(meta.get("dataset_id"), str) or not meta["dataset_id"].strip():
        raise ValueError("dataset_id required")
    if meta["source_kind"] == "measured" and (
        not isinstance(meta.get("collection_protocol"), str)
        or not meta["collection_protocol"].strip()
    ):
        raise ValueError("measured source requires collection_protocol")
    digest = hashlib.sha256(Path(trace_path).read_bytes()).hexdigest()
    if meta.get("trace_sha256") != digest:
        raise ValueError("trace SHA256 mismatch; reject modified or misidentified input")
    return meta, digest


def evaluate(catalog_path, trace_path, provenance_path):
    meta, digest = check_provenance(provenance_path, trace_path)
    rows = load_catalog(catalog_path)
    runs = load_complete_runs(trace_path)
    selected = policies(rows)
    a, b = selected["dp50"], selected["exact400"]
    gaps = []
    per_run = []
    for run_id, durations in runs.items():
        factors = [duration / rows[i][2] for i, duration in enumerate(durations)]
        score_a = realized(rows, a, factors)
        score_b = realized(rows, b, factors)
        gap = score_a - score_b
        gaps.append(gap)
        per_run.append({"run_id": run_id, "dp50": score_a, "exact400": score_b, "gap": gap})
    n = len(gaps)
    avg = mean(gaps)
    se = math.sqrt(sum((gap - avg) ** 2 for gap in gaps) / (n * (n - 1)))
    return {
        "experiment": "E513_COMPLETE_PAIRED_TRACE_REPLAY",
        "dataset_id": meta["dataset_id"],
        "source_kind": meta["source_kind"],
        "trace_sha256": digest,
        "run_count": n,
        "task_count": N_TASKS,
        "policies": {"dp50": a, "exact400": b},
        "miss_penalty": PENALTY,
        "mean_paired_gap": avg,
        "descriptive_paired_se": se,
        "per_run": per_run,
        "limitations": (
            "Input source_kind and collection protocol are self-reported, not authenticated. "
            "Complete runs allow counterfactual replay but do not establish task stationarity, "
            "independence of runs, latency causality or out-of-sample generalization. "
            "Synthetic inputs are tests, never empirical validation."
        ),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog")
    parser.add_argument("traces")
    parser.add_argument("provenance")
    args = parser.parse_args()
    print(json.dumps(evaluate(args.catalog, args.traces, args.provenance), indent=2))
