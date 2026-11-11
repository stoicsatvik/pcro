"""E519: same-source sensitivity audit of the E518 run-order association."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from research.e518_run_order_confound import (
    RUN_IDS,
    TASK_IDS,
    _validate_inputs,
    sha256_bytes,
)

DEFAULT_PERMUTATIONS = 9_999
DEFAULT_SEED = 20_261_112


class SensitivityError(ValueError):
    pass


def _double_center(values: np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=np.float64)
    return (
        matrix
        - matrix.mean(axis=0, keepdims=True)
        - matrix.mean(axis=1, keepdims=True)
        + matrix.mean()
    )


def _balanced_slope(outcome: np.ndarray, position: np.ndarray) -> float:
    if outcome.shape != position.shape or outcome.ndim != 2:
        raise SensitivityError("outcome and position matrices must have identical 2-D shapes")
    y = _double_center(outcome)
    x = _double_center(position)
    denominator = float(np.sum(x * x))
    if denominator <= 0:
        raise SensitivityError("position has zero residual variance after fixed effects")
    return float(np.sum(y * x) / denominator)


def _average_rank_columns(values: np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=np.float64)
    if matrix.ndim != 2 or not np.isfinite(matrix).all():
        raise SensitivityError("rank input must be a finite 2-D matrix")
    ranks = np.empty_like(matrix)
    for column in range(matrix.shape[1]):
        order = np.argsort(matrix[:, column], kind="mergesort")
        ordered = matrix[order, column]
        start = 0
        while start < len(order):
            end = start + 1
            while end < len(order) and ordered[end] == ordered[start]:
                end += 1
            average = (start + 1 + end) / 2.0
            ranks[order[start:end], column] = average
            start = end
    return ranks


def _unbalanced_fixed_effect_slope(
    outcome: np.ndarray,
    position: np.ndarray,
    run_ids: np.ndarray,
    task_ids: np.ndarray,
) -> float:
    y = np.asarray(outcome, dtype=np.float64).reshape(-1)
    x = np.asarray(position, dtype=np.float64).reshape(-1)
    runs = np.asarray(run_ids).reshape(-1)
    tasks = np.asarray(task_ids).reshape(-1)
    if not (len(y) == len(x) == len(runs) == len(tasks)) or len(y) == 0:
        raise SensitivityError("unbalanced fixed-effect vectors must be non-empty and equal length")
    if not (np.isfinite(y).all() and np.isfinite(x).all()):
        raise SensitivityError("unbalanced fixed-effect inputs must be finite")

    run_levels = list(dict.fromkeys(runs.tolist()))
    task_levels = list(dict.fromkeys(tasks.tolist()))
    run_columns = [(runs == level).astype(np.float64) for level in run_levels[1:]]
    task_columns = [(tasks == level).astype(np.float64) for level in task_levels[1:]]
    design = np.column_stack([np.ones(len(y)), *run_columns, *task_columns, x])
    coefficients, *_ = np.linalg.lstsq(design, y, rcond=None)
    return float(coefficients[-1])


def analyze(
    durations_ms: np.ndarray,
    positions: np.ndarray,
    *,
    permutations: int = DEFAULT_PERMUTATIONS,
    seed: int = DEFAULT_SEED,
) -> dict:
    durations = np.asarray(durations_ms, dtype=np.float64)
    position = np.asarray(positions, dtype=np.float64)
    expected = (len(RUN_IDS), len(TASK_IDS))
    if durations.shape != expected or position.shape != expected:
        raise SensitivityError(f"E519 requires the frozen {expected[0]}×{expected[1]} panel")
    if not np.isfinite(durations).all() or (durations <= 0).any():
        raise SensitivityError("durations must be finite and positive")
    if not np.isfinite(position).all() or permutations < 999:
        raise SensitivityError("positions must be finite and permutations must be at least 999")

    log_duration = np.log(durations)
    base_slope = _balanced_slope(log_duration, position)

    leave_one_task_out = {
        str(task_id): _balanced_slope(
            np.delete(log_duration, task_id, axis=1),
            np.delete(position, task_id, axis=1),
        )
        for task_id in TASK_IDS
    }

    run_grid = np.broadcast_to(np.arange(len(RUN_IDS))[:, None], expected)
    task_grid = np.broadcast_to(np.arange(len(TASK_IDS))[None, :], expected)
    trimmed_slopes = {}
    for count in range(1, 6):
        for side in ("first", "last"):
            keep = position >= (count / (len(TASK_IDS) - 1)) if side == "first" else (
                position <= ((len(TASK_IDS) - 1 - count) / (len(TASK_IDS) - 1))
            )
            trimmed_slopes[f"drop_{side}_{count}"] = _unbalanced_fixed_effect_slope(
                log_duration[keep],
                position[keep],
                run_grid[keep],
                task_grid[keep],
            )

    rank_outcome = _average_rank_columns(log_duration)
    rank_slope = _balanced_slope(rank_outcome, position)

    rng = np.random.default_rng(seed)
    log_residual = _double_center(log_duration)
    rank_residual = _double_center(rank_outcome)
    log_null = np.empty(permutations, dtype=np.float64)
    rank_null = np.empty(permutations, dtype=np.float64)
    for index in range(permutations):
        shuffled_position = np.vstack([rng.permutation(row) for row in position])
        shuffled_residual = _double_center(shuffled_position)
        denominator = float(np.sum(shuffled_residual * shuffled_residual))
        log_null[index] = float(np.sum(log_residual * shuffled_residual) / denominator)
        rank_null[index] = float(np.sum(rank_residual * shuffled_residual) / denominator)

    log_permutation_p = float(
        (1 + np.count_nonzero(np.abs(log_null) >= abs(base_slope))) / (permutations + 1)
    )
    rank_permutation_p = float(
        (1 + np.count_nonzero(np.abs(rank_null) >= abs(rank_slope))) / (permutations + 1)
    )

    task_means = log_duration.mean(axis=0)
    run_slopes = {}
    for index, run_id in enumerate(RUN_IDS):
        adjusted = log_duration[index] - task_means
        centered_position = position[index] - position[index].mean()
        run_slopes[run_id] = float(
            np.sum(centered_position * adjusted) / np.sum(centered_position * centered_position)
        )

    loo_values = np.asarray(list(leave_one_task_out.values()), dtype=np.float64)
    trimmed_values = np.asarray(list(trimmed_slopes.values()), dtype=np.float64)
    return {
        "experiment": "E519 same-source run-order sensitivity audit",
        "status": "COMPLETE",
        "cohort": {"runs": len(RUN_IDS), "tasks_per_run": len(TASK_IDS), "observations": int(durations.size)},
        "primary_reproduction": {
            "e518_log_duration_slope": base_slope,
            "within_run_permutation_p": log_permutation_p,
            "permutation_count": permutations,
            "permutation_seed": seed,
        },
        "leave_one_task_out": {
            "task_count": len(leave_one_task_out),
            "all_slopes_negative": bool(np.all(loo_values < 0)),
            "minimum_slope": float(loo_values.min()),
            "maximum_slope": float(loo_values.max()),
            "slopes_by_task_id": leave_one_task_out,
        },
        "position_trimming": {
            "all_slopes_negative": bool(np.all(trimmed_values < 0)),
            "minimum_slope": float(trimmed_values.min()),
            "maximum_slope": float(trimmed_values.max()),
            "slopes": trimmed_slopes,
            "interpretation": "same-data sensitivity only; no independent replication",
        },
        "within_task_rank_sensitivity": {
            "rank_slope_per_full_run": rank_slope,
            "within_run_permutation_p": rank_permutation_p,
            "permutation_count": permutations,
            "permutation_seed": seed,
            "interpretation": (
                "exploratory same-data rank sensitivity; not independent confirmation "
                "and not a calibrated probability of a physical mechanism"
            ),
        },
        "run_specific_log_slopes": run_slopes,
        "run_slope_signs": {
            "negative": int(sum(value < 0 for value in run_slopes.values())),
            "positive": int(sum(value > 0 for value in run_slopes.values())),
            "zero": int(sum(value == 0 for value in run_slopes.values())),
        },
        "claim_boundary": {
            "single_host_order_association": "SUPPORTED AS A ROBUST SAME-DATA CANDIDATE CONFOUND",
            "causal_mechanism": "NOT IDENTIFIED",
            "independent_host_replication": "NOT MEASURED",
            "real_task_scheduler_effect": "NOT PROVEN",
        },
        "limitations": [
            "All sensitivity checks reuse the same 144 observations from one container host.",
            "Task deletion and position trimming are robustness checks, not independent samples.",
            "The rank permutation is exploratory and uses the same source observations.",
            "Five of six run-specific slopes are negative, but one is positive and run-level independence is not established.",
            "No timestamps, CPU-frequency, temperature, utilization, or host-level telemetry are present.",
            "The provenance source_kind and hashes are self-reported and do not independently authenticate measurement collection.",
        ],
    }


def run(
    traces_path: Path,
    catalog_path: Path,
    provenance_path: Path,
    *,
    permutations: int = DEFAULT_PERMUTATIONS,
    seed: int = DEFAULT_SEED,
) -> dict:
    durations, positions, provenance, trace_bytes, catalog_bytes = _validate_inputs(
        traces_path, catalog_path, provenance_path
    )
    result = analyze(durations, positions, permutations=permutations, seed=seed)
    result["source"] = {
        "dataset_id": provenance["dataset_id"],
        "source_kind": provenance["source_kind"],
        "source_kind_is_self_reported": True,
        "trace_sha256": sha256_bytes(trace_bytes),
        "catalog_sha256": sha256_bytes(catalog_bytes),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.traces, args.catalog, args.provenance)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "e518_slope": result["primary_reproduction"]["e518_log_duration_slope"],
                "leave_one_task_out_all_negative": result["leave_one_task_out"]["all_slopes_negative"],
                "trimmed_all_negative": result["position_trimming"]["all_slopes_negative"],
                "rank_permutation_p": result["within_task_rank_sensitivity"]["within_run_permutation_p"],
                "negative_run_slopes": result["run_slope_signs"]["negative"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
