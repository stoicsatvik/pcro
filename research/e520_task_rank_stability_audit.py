"""E520A: reconcile the task-rank stability statistic from pinned holdout rows.

Uses only the committed 6x24 E520 holdout CSV. Task identity is the stable
task_id key; duration ranks are recomputed within each run, then compared
pairwise across runs. No SciPy or external data is required.
"""
from __future__ import annotations

import argparse
import csv
import json
from itertools import combinations
from math import isfinite
from pathlib import Path

REQUIRED_COLUMNS = {"run_id", "task_id", "duration_ms"}


def average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        average = ((start + 1) + end) / 2.0
        for index in order[start:end]:
            ranks[index] = average
        start = end
    return ranks


def spearman(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        raise ValueError("Spearman inputs must have equal length >= 2")
    if not all(isfinite(value) for value in left + right):
        raise ValueError("Spearman inputs must be finite")
    a, b = average_ranks(left), average_ranks(right)
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    numerator = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a)
    db = sum((y - mb) ** 2 for y in b)
    if da <= 0 or db <= 0:
        raise ValueError("Spearman input has zero rank variance")
    return numerator / (da * db) ** 0.5


def _read_measurements(path: Path) -> list[dict]:
    """Read a strict, finite task-duration panel before any rank calculation."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        if not headers or any(not name or not name.strip() for name in headers):
            raise ValueError("holdout CSV has a missing or empty header")
        if len(headers) != len(set(headers)):
            raise ValueError("holdout CSV contains duplicate headers")
        missing = REQUIRED_COLUMNS - set(headers)
        if missing:
            raise ValueError(
                "holdout CSV is missing required columns: "
                + ", ".join(sorted(missing))
            )

        rows = []
        for line_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"holdout CSV row {line_number} has extra fields")
            if any(row.get(name) is None or not row[name].strip() for name in REQUIRED_COLUMNS):
                raise ValueError(f"holdout CSV row {line_number} has an empty required field")
            run_id = row["run_id"].strip()
            if not run_id:
                raise ValueError(f"holdout CSV row {line_number} has an empty run_id")
            try:
                task_id = int(row["task_id"])
                duration = float(row["duration_ms"])
            except ValueError as error:
                raise ValueError(
                    f"holdout CSV row {line_number} has a non-numeric task_id or duration"
                ) from error
            if not isfinite(duration):
                raise ValueError(
                    f"holdout CSV row {line_number} duration_ms must be finite"
                )
            if duration <= 0:
                raise ValueError(
                    f"holdout CSV row {line_number} duration_ms must be positive"
                )
            rows.append(
                {"run_id": run_id, "task_id": task_id, "duration_ms": duration}
            )
    return rows


def audit(path: Path) -> dict:
    rows = _read_measurements(path)
    if len(rows) != 144:
        raise ValueError(f"expected 144 holdout rows, found {len(rows)}")

    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row["run_id"], []).append(row)
    run_ids = sorted(groups)
    expected_tasks = set(range(24))
    if len(run_ids) != 6:
        raise ValueError(f"expected 6 holdout runs, found {len(run_ids)}")

    per_run = []
    task_duration_by_run = {}
    for run_id in run_ids:
        group = groups[run_id]
        task_ids = [row["task_id"] for row in group]
        if len(group) != 24 or set(task_ids) != expected_tasks:
            raise ValueError(f"{run_id} is not a complete 24-task panel")
        ordered = sorted(group, key=lambda row: row["task_id"])
        tasks = [row["task_id"] for row in ordered]
        durations = [row["duration_ms"] for row in ordered]
        task_duration_by_run[run_id] = dict(zip(tasks, durations))
        per_run.append(
            {
                "run_id": run_id,
                "n": len(group),
                "spearman_task_id_vs_duration": spearman(tasks, durations),
            }
        )

    pairwise = []
    for left, right in combinations(run_ids, 2):
        tasks = sorted(expected_tasks)
        rho = spearman(
            [task_duration_by_run[left][task] for task in tasks],
            [task_duration_by_run[right][task] for task in tasks],
        )
        pairwise.append({"run_a": left, "run_b": right, "spearman": rho})

    pair_values = sorted(item["spearman"] for item in pairwise)
    median = pair_values[len(pair_values) // 2]
    pooled_tasks = [row["task_id"] for row in rows]
    pooled_durations = [row["duration_ms"] for row in rows]
    pooled = spearman(pooled_tasks, pooled_durations)

    result = {
        "experiment": "E520A",
        "source_csv": "research/results/e520_holdout_measurements.csv",
        "rows": len(rows),
        "runs": len(run_ids),
        "tasks_per_run": 24,
        "within_run_task_id_duration_spearman": per_run,
        "pairwise_task_duration_rank_spearman": {
            "pairs": len(pairwise),
            "median": median,
            "minimum": pair_values[0],
            "maximum": pair_values[-1],
            "values": pairwise,
        },
        "pooled_task_id_duration_spearman": pooled,
        "legacy_reported_statistic": {
            "median": -0.12344267996967351,
            "range": [-0.7009541714096962, 0.43373512603284853],
            "status": "UNRESOLVED_NOT_REPRODUCED_UNDER_STANDARD_PAIRWISE_DURATION_RANK",
            "reason": (
                "The preregistration says task-rank stability but does not define "
                "the pairing/estimand; no committed analysis code reproduces this "
                "legacy statistic."
            ),
        },
        "interpretation": (
            "Under the conventional definition of pairwise task-duration rank "
            "stability keyed by task_id, ranks are highly stable across the six "
            "holdout runs. The legacy negative statistic is unresolved and must "
            "not be used as evidence of unstable task costs. The E520 primary "
            "execution-position slope and permutation result are unchanged."
        ),
        "validation": {
            "complete_panel": True,
            "all_pairwise_rank_correlations_above_0_93": all(
                value > 0.93 for value in pair_values
            ),
            "no_specimen_or_source_rows_added": True,
        },
    }

    assert len(pairwise) == 15
    assert all(value > 0.93 for value in pair_values)
    assert abs(median - 0.9956521739130435) < 1e-12
    assert abs(pair_values[0] - 0.9382608695652174) < 1e-12
    assert abs(pair_values[-1] - 1.0) < 1e-12
    assert abs(pooled - 0.9846510089368863) < 1e-12
    assert all(item["spearman_task_id_vs_duration"] >= 0.95 for item in per_run)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("research/results/e520_holdout_measurements.csv"),
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit(args.csv)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
