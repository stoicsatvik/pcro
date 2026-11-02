"""E516: predeclared fresh measured CPU stress cohort, not deployment evidence.

The 3/2 iteration multiplier is frozen from E515's exploratory pilot before
any E516 timings are observed. Never select a multiplier using E516 holdouts.
"""
import argparse
import csv
import hashlib
import json
import os
import platform
import random
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path

from research.e507_gaussian_copula import policies
from research.e513_trace_replay import evaluate
from research.e515_measured_trace_collector import N_TASKS, task_rounds, workload

SCALE_NUMERATOR = 3
SCALE_DENOMINATOR = 2
ORDER_SEED = 0xE5162026
DATASET_ID = "E516_CPU_SHA256_FRESH_STRESS"


def scaled_rounds(task_id):
    """Exact integer half-up rounding, independent of platform float behavior."""
    original = task_rounds(task_id)
    return (original * SCALE_NUMERATOR + SCALE_DENOMINATOR // 2) // SCALE_DENOMINATOR


def policy_gate(nominals):
    """Only calibration costs enter this selection; holdouts remain unseen."""
    if len(nominals) != N_TASKS or any(type(v) is not int or v < 1 for v in nominals):
        raise ValueError("requires 24 positive integer calibration costs")
    rewards = [5 + ((i * 37 + 2026) % 96) for i in range(N_TASKS)]
    rows = [(i, rewards[i], nominals[i]) for i in range(N_TASKS)]
    selected = policies(rows)
    return {
        "dp50": selected["dp50"],
        "exact400": selected["exact400"],
        "divergent": selected["dp50"] != selected["exact400"],
        "nominal_total_ms": sum(nominals),
    }


def _write_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(destination, *, warmups=1, calibrations=3, holdouts=6,
            seed=ORDER_SEED, source_kind="measured"):
    if type(warmups) is not int or type(calibrations) is not int or type(holdouts) is not int:
        raise ValueError("run counts must be integers")
    if warmups < 0 or calibrations < 2 or holdouts < 2:
        raise ValueError("requires >=0 warmups, >=2 calibrations, >=2 holdouts")
    if source_kind not in ("measured", "synthetic"):
        raise ValueError("invalid source_kind")
    out = Path(destination)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise FileExistsError("destination must be an empty directory")
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    calibration = {i: [] for i in range(N_TASKS)}
    holdout_rows = []
    order_log = []
    digest_log = {}
    gate = None
    nominals = None
    for phase, count in (("warmup", warmups), ("calibration", calibrations), ("holdout", holdouts)):
        if phase == "holdout":
            # Pre-holdout freeze: no observed holdout duration can change this gate.
            nominals = [max(1, round(statistics.median(calibration[i]))) for i in range(N_TASKS)]
            gate = policy_gate(nominals)
        for index in range(count):
            run_id = f"{phase}-{index:03d}"
            order = list(range(N_TASKS))
            rng.shuffle(order)
            order_log.append({"run_id": run_id, "task_order": order})
            for task_id in order:
                before = time.perf_counter_ns()
                digest = workload(task_id, scaled_rounds(task_id))
                elapsed = time.perf_counter_ns() - before
                if elapsed <= 0:
                    raise RuntimeError("nonpositive elapsed time")
                if task_id in digest_log and digest_log[task_id] != digest:
                    raise RuntimeError("nondeterministic workload output")
                digest_log[task_id] = digest
                duration_ms = elapsed / 1_000_000
                if phase == "calibration":
                    calibration[task_id].append(duration_ms)
                elif phase == "holdout":
                    holdout_rows.append((run_id, task_id, f"{duration_ms:.6f}"))
    assert nominals is not None and gate is not None
    rewards = [5 + ((i * 37 + 2026) % 96) for i in range(N_TASKS)]
    catalog = out / "catalog.csv"
    traces = out / "holdout_traces.csv"
    provenance = out / "provenance.json"
    _write_csv(catalog, ("task_id", "reward", "nominal_ms"),
               ((i, rewards[i], nominals[i]) for i in range(N_TASKS)))
    _write_csv(traces, ("run_id", "task_id", "duration_ms"), holdout_rows)
    meta = {
        "dataset_id": DATASET_ID,
        "source_kind": source_kind,
        "time_unit": "ms",
        "collection_protocol": "Predeclared 3/2 E515 SHA256 rounds; randomized order; warmup then calibration-only policy gate, then complete holdouts",
        "collected_at_utc": datetime.now(UTC).isoformat(),
        "trace_sha256": _sha(traces),
        "catalog_sha256": _sha(catalog),
        "collector_sha256": _sha(Path(__file__)),
        "scale_numerator": SCALE_NUMERATOR,
        "scale_denominator": SCALE_DENOMINATOR,
        "rounds_by_task": [scaled_rounds(i) for i in range(N_TASKS)],
        "task_output_sha256_hex": [digest_log[i] for i in range(N_TASKS)],
        "pre_holdout_gate": gate,
        "reward_source": "E515 frozen arbitrary synthetic rewards, not economic value",
        "nominal_source": "rounded median of E516 calibration timings only",
        "warmup_runs": warmups,
        "calibration_runs": calibrations,
        "holdout_runs": holdouts,
        "order_seed": seed,
        "run_orders": order_log,
        "environment": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "system": platform.system(),
            "machine": platform.machine(),
            "cpu_count_visible": os.cpu_count(),
            "perf_counter_resolution_seconds": time.get_clock_info("perf_counter").resolution,
        },
        "limitations": "Exploratory single-host CPU microbenchmark with synthetic rewards. "
                       "The E515 pilot informed the predeclared 3/2 multiplier; E516 is not independent of that design choice. "
                       "Calibration and holdouts share host; unknown contention/thermal state; "
                       "randomization does not guarantee independent trials; no policy overhead measured; "
                       "self-reported hashes and provenance do not authenticate the measurements.",
    }
    provenance.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = evaluate(catalog, traces, provenance)
    return {"provenance": meta, "replay": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E516 frozen CPU stress cohort")
    parser.add_argument("output_dir")
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--calibrations", type=int, default=3)
    parser.add_argument("--holdouts", type=int, default=6)
    args = parser.parse_args()
    print(json.dumps(collect(args.output_dir, warmups=args.warmups,
                             calibrations=args.calibrations, holdouts=args.holdouts), indent=2))
