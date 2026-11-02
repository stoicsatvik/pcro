"""E515: bounded CPU-only pilot trace collection for E513 paired replay.

This is a reproducible measurement protocol, NOT a representative PCRO benchmark.
Synthetic rewards and calibration-derived nominal costs cannot establish deployment utility.
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
from datetime import datetime, timezone
from pathlib import Path

N_TASKS = 24
ORDER_SEED = 0xE5152026


def task_rounds(task_id):
    if not isinstance(task_id, int) or not 0 <= task_id < N_TASKS:
        raise ValueError("task_id must be 0..23")
    return 8000 + 2200 * task_id


def workload(task_id, rounds=None):
    """Serial dependent SHA256 chain, fixed deterministic input; no external I/O."""
    count = task_rounds(task_id) if rounds is None else rounds
    if not isinstance(count, int) or count < 1:
        raise ValueError("rounds must be a positive integer")
    state = bytes([task_id]) * 32
    payload = bytes([task_id ^ 0xA5]) * 128
    for _ in range(count):
        state = hashlib.sha256(state + payload).digest()
    return state.hex()


def _write_csv(path, columns, records):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(records)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(destination, *, warmups=1, calibrations=3, holdouts=6, seed=ORDER_SEED,
            rounds_override=None, source_kind="measured"):
    """Measure all tasks every run. Calibrate before frozen holdout replay.

    The caller must not infer independence or task representativeness from this output.
    source_kind='synthetic' is reserved for mocked-clock/unit-test runs.
    """
    if warmups < 0 or calibrations < 2 or holdouts < 2:
        raise ValueError("requires >=0 warmups, >=2 calibrations, >=2 holdouts")
    if source_kind not in ("measured", "synthetic"):
        raise ValueError("invalid source_kind")
    if rounds_override is not None and (not isinstance(rounds_override, int) or rounds_override < 1):
        raise ValueError("rounds_override must be a positive integer")
    out = Path(destination)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("destination must be empty; never overwrite measurement evidence")
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    calibration = {i: [] for i in range(N_TASKS)}
    holdout_rows = []
    order_log = []
    digest_log = {}
    for phase, count in (("warmup", warmups), ("calibration", calibrations), ("holdout", holdouts)):
        for index in range(count):
            run_id = f"{phase}-{index:03d}"
            order = list(range(N_TASKS))
            rng.shuffle(order)
            order_log.append({"run_id": run_id, "task_order": order})
            for task_id in order:
                before = time.perf_counter_ns()
                digest = workload(task_id, rounds_override)
                elapsed = time.perf_counter_ns() - before
                if elapsed <= 0:
                    raise RuntimeError("nonpositive clock interval; cannot measure")
                duration_ms = elapsed / 1_000_000
                if task_id in digest_log and digest_log[task_id] != digest:
                    raise RuntimeError("nondeterministic task output")
                digest_log[task_id] = digest
                if phase == "calibration":
                    calibration[task_id].append(duration_ms)
                elif phase == "holdout":
                    holdout_rows.append((run_id, task_id, f"{duration_ms:.6f}"))
    # Median calibration is frozen before any holdout data enter the task catalog.
    # ceil is unnecessary: nearest integer milliseconds, with a strict lower bound.
    nominal = [max(1, round(statistics.median(calibration[i]))) for i in range(N_TASKS)]
    # Deterministic synthetic rewards, NOT economic/task values.
    rewards = [5 + ((i * 37 + 2026) % 96) for i in range(N_TASKS)]
    catalog = out / "catalog.csv"
    traces = out / "holdout_traces.csv"
    provenance = out / "provenance.json"
    _write_csv(catalog, ("task_id", "reward", "nominal_ms"),
               ((i, rewards[i], nominal[i]) for i in range(N_TASKS)))
    _write_csv(traces, ("run_id", "task_id", "duration_ms"), holdout_rows)
    protocol = {
        "dataset_id": "E515_CPU_SHA256_PILOT",
        "source_kind": source_kind,
        "time_unit": "ms",
        "collection_protocol": "serial dependent SHA256 CPU tasks; randomized order; warmup, calibration, then held-out complete runs",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "trace_sha256": _sha(traces),
        "catalog_sha256": _sha(catalog),
        "collector_sha256": _sha(Path(__file__)),
        "task_definition": "state=SHA256(state||128-byte payload), repeated fixed rounds per task",
        "rounds_by_task": [rounds_override or task_rounds(i) for i in range(N_TASKS)],
        "task_output_sha256_hex": [digest_log[i] for i in range(N_TASKS)],
        "reward_source": "arbitrary deterministic synthetic rewards, not measured value",
        "nominal_source": "rounded median of calibration timings; not tuned on holdout",
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
        "limitations": "Exploratory local CPU microbenchmark only. Unknown host contention/thermal state; "
                       "calibration and holdout share a host; randomization does not ensure independence; "
                       "all tasks run serially; policy-specific contention and scheduling overhead not measured; "
                       "self-reported provenance and arbitrary rewards do not establish real-world utility.",
    }
    provenance.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return protocol


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E515 CPU-only complete paired trace pilot")
    parser.add_argument("output_dir")
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--calibrations", type=int, default=3)
    parser.add_argument("--holdouts", type=int, default=6)
    args = parser.parse_args()
    print(json.dumps(collect(args.output_dir, warmups=args.warmups,
                             calibrations=args.calibrations, holdouts=args.holdouts), indent=2))
