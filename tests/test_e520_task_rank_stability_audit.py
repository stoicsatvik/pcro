import csv
from pathlib import Path

import pytest

from research.e520_task_rank_stability_audit import audit, spearman


def _write_panel(path: Path, *, bad_duration: str | None = None, extra_field: bool = False) -> None:
    headers = ["run_id", "task_id", "duration_ms"]
    if extra_field:
        headers.append("unexpected")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for run in range(6):
            for task in range(24):
                duration = str(float(task + 1) + run * 0.001)
                if (run, task) == (0, 0) and bad_duration is not None:
                    duration = bad_duration
                row = [f"run-{run}", task, duration]
                if extra_field:
                    row.append("unexpected-value")
                writer.writerow(row)


@pytest.mark.parametrize("bad_duration", ["nan", "inf", "-inf"])
def test_audit_rejects_non_finite_durations(tmp_path: Path, bad_duration: str) -> None:
    path = tmp_path / "measurements.csv"
    _write_panel(path, bad_duration=bad_duration)

    with pytest.raises(ValueError, match="duration_ms must be finite"):
        audit(path)


def test_audit_rejects_duplicate_headers(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["run_id", "task_id", "duration_ms", "duration_ms"])
        for run in range(6):
            for task in range(24):
                writer.writerow([f"run-{run}", task, task + 1, task + 1])

    with pytest.raises(ValueError, match="duplicate headers"):
        audit(path)


def test_audit_rejects_missing_required_headers(tmp_path: Path) -> None:
    path = tmp_path / "missing.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["run_id", "task_id"])
        for run in range(6):
            for task in range(24):
                writer.writerow([f"run-{run}", task])

    with pytest.raises(ValueError, match="missing required columns"):
        audit(path)


def test_audit_rejects_extra_row_fields(tmp_path: Path) -> None:
    path = tmp_path / "extra.csv"
    _write_panel(path, extra_field=True)
    # The named extra column is allowed; an unheaded extra value is not.
    rows = path.read_text(encoding="utf-8").splitlines()
    rows[1] += ",unheaded"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="has extra fields"):
        audit(path)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_spearman_rejects_non_finite_inputs(bad: float) -> None:
    with pytest.raises(ValueError, match="must be finite"):
        spearman([1.0, 2.0, bad], [1.0, 2.0, 3.0])


def test_spearman_keeps_finite_rank_result_unchanged() -> None:
    assert spearman([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)
