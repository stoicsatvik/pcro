"""E518: audit run-order drift in the pinned E516 measured CPU trace cohort."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

RUN_IDS = tuple(f"holdout-{i:03d}" for i in range(6))
TASK_IDS = tuple(range(24))
N_PERMUTATIONS = 9999
PERMUTATION_SEED = 20261111
TRACE_HEADER = ("run_id", "task_id", "duration_ms")
CATALOG_HEADER = ("task_id", "reward", "nominal_ms")


class AuditError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_csv(path: Path, expected_header: tuple[str, ...]) -> tuple[bytes, list[dict[str, str]]]:
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    if tuple(reader.fieldnames or ()) != expected_header:
        raise AuditError(f"{path.name}: unexpected CSV header")
    return raw, list(reader)


def _validate_inputs(traces_path: Path, catalog_path: Path, provenance_path: Path):
    trace_bytes, trace_rows = _read_csv(traces_path, TRACE_HEADER)
    catalog_bytes, catalog_rows = _read_csv(catalog_path, CATALOG_HEADER)
    provenance = json.loads(Path(provenance_path).read_text(encoding="utf-8"))

    if provenance.get("dataset_id") != "E516_CPU_SHA256_FRESH_STRESS":
        raise AuditError("unexpected E516 dataset_id")
    if provenance.get("source_kind") != "measured" or provenance.get("time_unit") != "ms":
        raise AuditError("E516 source_kind/time_unit contract mismatch")
    if provenance.get("trace_sha256") != sha256_bytes(trace_bytes):
        raise AuditError("E516 trace digest mismatch")
    if provenance.get("catalog_sha256") != sha256_bytes(catalog_bytes):
        raise AuditError("E516 catalog digest mismatch")

    catalog: dict[int, dict[str, float]] = {}
    for row in catalog_rows:
        task_id = int(row["task_id"])
        reward = int(row["reward"])
        nominal_ms = float(row["nominal_ms"])
        if task_id in catalog or reward <= 0 or not np.isfinite(nominal_ms) or nominal_ms <= 0:
            raise AuditError("invalid or duplicate E516 catalog row")
        catalog[task_id] = {"reward": reward, "nominal_ms": nominal_ms}
    if tuple(sorted(catalog)) != TASK_IDS:
        raise AuditError("E516 catalog must contain task IDs 0..23 exactly")

    durations = np.full((len(RUN_IDS), len(TASK_IDS)), np.nan, dtype=np.float64)
    positions = np.full_like(durations, np.nan)
    seen = {run_id: set() for run_id in RUN_IDS}
    run_order = []
    last_run = None
    position_by_run = {run_id: 0 for run_id in RUN_IDS}

    for row in trace_rows:
        run_id = row["run_id"]
        if run_id not in seen:
            raise AuditError(f"unexpected run_id: {run_id}")
        if last_run != run_id:
            if run_id in run_order:
                raise AuditError("trace rows for each run must be contiguous")
            run_order.append(run_id)
            last_run = run_id
        task_id = int(row["task_id"])
        duration = float(row["duration_ms"])
        if task_id not in catalog or task_id in seen[run_id]:
            raise AuditError("unexpected or duplicate task in an E516 run")
        if not np.isfinite(duration) or duration <= 0:
            raise AuditError("duration_ms must be finite and positive")
        index = RUN_IDS.index(run_id)
        durations[index, task_id] = duration
        positions[index, task_id] = position_by_run[run_id] / (len(TASK_IDS) - 1)
        position_by_run[run_id] += 1
        seen[run_id].add(task_id)

    if tuple(run_order) != RUN_IDS:
        raise AuditError("E516 run order or run population differs from the frozen six-run cohort")
    if any(tasks != set(TASK_IDS) for tasks in seen.values()):
        raise AuditError("every E516 run must contain all 24 tasks exactly once")
    if not np.isfinite(durations).all() or not np.isfinite(positions).all():
        raise AuditError("E516 trace contains missing task/run cells")
    return durations, positions, provenance, trace_bytes, catalog_bytes


def _double_center(matrix: np.ndarray) -> np.ndarray:
    """Remove additive task and run fixed effects from a balanced run×task matrix."""
    return (
        matrix
        - matrix.mean(axis=0, keepdims=True)
        - matrix.mean(axis=1, keepdims=True)
        + matrix.mean()
    )


def _slope(y_residual: np.ndarray, x_residual: np.ndarray) -> float:
    denominator = float(np.sum(x_residual * x_residual))
    if denominator <= 0:
        raise AuditError("run-order feature has zero residual variance")
    return float(np.sum(x_residual * y_residual) / denominator)


def _rank(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=np.float64)
    ranks[order] = np.arange(1, len(values) + 1, dtype=np.float64)
    return ranks


def analyze(durations_ms: np.ndarray, positions: np.ndarray, *, n_permutations: int = N_PERMUTATIONS,
            seed: int = PERMUTATION_SEED) -> dict:
    if durations_ms.shape != (6, 24) or positions.shape != (6, 24):
        raise AuditError("E518 requires the frozen 6×24 balanced E516 panel")
    if n_permutations < 999:
        raise AuditError("at least 999 within-run permutations are required")
    if not np.isfinite(durations_ms).all() or (durations_ms <= 0).any():
        raise AuditError("durations must be finite and positive")

    log_duration = np.log(durations_ms)
    y_residual = _double_center(log_duration)
    x_residual = _double_center(positions)
    beta = _slope(y_residual, x_residual)
    sse_without_order = float(np.sum(y_residual * y_residual))
    residual_after_order = y_residual - beta * x_residual
    sse_with_order = float(np.sum(residual_after_order * residual_after_order))
    partial_r2 = (sse_without_order - sse_with_order) / sse_without_order

    rng = np.random.default_rng(seed)
    null_betas = np.empty(n_permutations, dtype=np.float64)
    for index in range(n_permutations):
        shuffled = np.vstack([rng.permutation(row) for row in positions])
        null_betas[index] = _slope(y_residual, _double_center(shuffled))
    p_value = float((1 + np.count_nonzero(np.abs(null_betas) >= abs(beta))) / (n_permutations + 1))

    task_means = log_duration.mean(axis=0)
    run_slopes = {}
    for run_index, run_id in enumerate(RUN_IDS):
        adjusted = log_duration[run_index] - task_means
        centered_position = positions[run_index] - positions[run_index].mean()
        run_slopes[run_id] = float(
            np.sum(centered_position * adjusted) / np.sum(centered_position * centered_position)
        )

    leave_one_run_out = {}
    for omitted, run_id in enumerate(RUN_IDS):
        keep = np.arange(len(RUN_IDS)) != omitted
        y_loo = log_duration[keep]
        x_loo = positions[keep]
        leave_one_run_out[run_id] = _slope(_double_center(y_loo), _double_center(x_loo))

    rank_correlations = []
    for left, right in itertools.combinations(range(len(RUN_IDS)), 2):
        rank_correlations.append(float(np.corrcoef(_rank(durations_ms[left]), _rank(durations_ms[right]))[0, 1]))

    total_ss = float(np.sum((log_duration - log_duration.mean()) ** 2))
    task_only_residual = log_duration - log_duration.mean(axis=0, keepdims=True)
    run_only_residual = log_duration - log_duration.mean(axis=1, keepdims=True)
    r2_task = 1.0 - float(np.sum(task_only_residual ** 2)) / total_ss
    r2_run = 1.0 - float(np.sum(run_only_residual ** 2)) / total_ss
    r2_task_run = 1.0 - sse_without_order / total_ss
    r2_task_run_order = 1.0 - sse_with_order / total_ss

    coefficients = {
        "log_duration_slope_per_full_run": beta,
        "multiplicative_first_to_last": float(np.exp(beta)),
        "partial_r2_after_task_and_run_fixed_effects": float(partial_r2),
        "permutation_p_two_sided": p_value,
        "null_beta_95_percentile": [float(v) for v in np.quantile(null_betas, [0.025, 0.975])],
        "permutation_count": int(n_permutations),
        "permutation_seed": int(seed),
        "run_specific_log_slopes": run_slopes,
        "leave_one_run_out_log_slopes": leave_one_run_out,
    }
    return {
        "experiment": "E518 E516 CPU trace run-order confound audit",
        "status": "COMPLETE",
        "cohort": {"runs": len(RUN_IDS), "tasks_per_run": len(TASK_IDS), "observations": int(durations_ms.size)},
        "model": "log(duration_ms) ~ task fixed effects + run fixed effects + normalized execution position",
        "run_order_effect": coefficients,
        "variance_decomposition_r2": {
            "task_only": float(r2_task),
            "run_only": float(r2_run),
            "task_plus_run": float(r2_task_run),
            "task_plus_run_plus_order": float(r2_task_run_order),
        },
        "task_rank_stability": {
            "median_pairwise_spearman": float(np.median(rank_correlations)),
            "minimum_pairwise_spearman": float(np.min(rank_correlations)),
            "maximum_pairwise_spearman": float(np.max(rank_correlations)),
        },
        "median_task_coefficient_of_variation_across_runs": float(
            np.median(durations_ms.std(axis=0, ddof=1) / durations_ms.mean(axis=0))
        ),
        "run_total_duration_ms": {
            run_id: float(durations_ms[index].sum()) for index, run_id in enumerate(RUN_IDS)
        },
        "claim_boundary": {
            "order_association_in_pinned_single_host_microbenchmark": (
                "CANDIDATE CONFOUND" if p_value < 0.05 else "NOT DETECTED AT THE FROZEN TEST"
            ),
            "causal_mechanism": "NOT IDENTIFIED",
            "multi_host_reproducibility": "NOT MEASURED",
            "real_task_scheduler_superiority": "NOT PROVEN",
        },
        "limitations": [
            "Six holdout runs from one container host; the six runs are not independent machines.",
            "The workload is a SHA256 CPU microbenchmark and rewards are synthetic.",
            "Execution position is CSV row order; timestamps and hardware telemetry are absent.",
            "The within-run permutation assumes randomized task order under the no-order-effect null.",
            "A detected order association does not identify warmup, cache, frequency, thermal or contention mechanisms.",
            "No policy overhead or scheduler-induced contention was measured.",
        ],
    }


def run(traces_path: Path, catalog_path: Path, provenance_path: Path) -> dict:
    durations, positions, provenance, trace_bytes, catalog_bytes = _validate_inputs(
        traces_path, catalog_path, provenance_path
    )
    result = analyze(durations, positions)
    result["source"] = {
        "dataset_id": provenance["dataset_id"],
        "source_kind": provenance["source_kind"],
        "source_kind_is_self_reported": True,
        "trace_sha256": sha256_bytes(trace_bytes),
        "catalog_sha256": sha256_bytes(catalog_bytes),
        "collection_protocol": provenance.get("collection_protocol"),
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
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "observations": result["cohort"]["observations"],
        "log_slope": result["run_order_effect"]["log_duration_slope_per_full_run"],
        "first_to_last_ratio": result["run_order_effect"]["multiplicative_first_to_last"],
        "partial_r2": result["run_order_effect"]["partial_r2_after_task_and_run_fixed_effects"],
        "permutation_p": result["run_order_effect"]["permutation_p_two_sided"],
        "median_pairwise_spearman": result["task_rank_stability"]["median_pairwise_spearman"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
