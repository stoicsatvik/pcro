"""E515 collector controls. Mocked tiny workloads are NOT real measurements."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.e513_trace_replay import evaluate
from research.e515_measured_trace_collector import N_TASKS, collect, task_rounds, workload


class CollectorTests(unittest.TestCase):
    def test_workload_deterministic_and_distinct(self):
        self.assertEqual(workload(0, 2), workload(0, 2))
        self.assertNotEqual(workload(0, 2), workload(1, 2))
        self.assertEqual(len(workload(0, 2)), 64)
        self.assertGreater(task_rounds(23), task_rounds(0))

    def test_invalid_task_and_rounds_rejected(self):
        for task in (-1, 24, "0"):
            with self.subTest(task=task), self.assertRaises(ValueError):
                task_rounds(task)
        with self.assertRaises(ValueError):
            workload(0, 0)

    def test_complete_holdout_and_catalog_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "pilot"
            with patch("research.e515_measured_trace_collector.workload", side_effect=lambda i, rounds: f"digest{i}"):
                manifest = collect(output, warmups=1, calibrations=2, holdouts=2,
                                   rounds_override=1, source_kind="synthetic")
            with (output / "holdout_traces.csv").open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            with (output / "catalog.csv").open(newline="", encoding="utf-8") as f:
                catalog = list(csv.DictReader(f))
            self.assertEqual(len(rows), N_TASKS * 2)
            self.assertEqual(len(catalog), N_TASKS)
            self.assertEqual({row["run_id"] for row in rows}, {"holdout-000", "holdout-001"})
            self.assertEqual({int(row["task_id"]) for row in rows}, set(range(N_TASKS)))
            self.assertEqual(manifest["source_kind"], "synthetic")
            self.assertEqual(manifest["calibration_runs"], 2)
            self.assertEqual(len(manifest["run_orders"]), 5)
            self.assertEqual(manifest["trace_sha256"], hashlib.sha256((output / "holdout_traces.csv").read_bytes()).hexdigest())
            self.assertEqual(manifest["catalog_sha256"], hashlib.sha256((output / "catalog.csv").read_bytes()).hexdigest())
            self.assertEqual(json.loads((output / "provenance.json").read_text())["dataset_id"], "E515_CPU_SHA256_PILOT")

    def test_collector_output_passes_e513_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "pilot"
            with patch("research.e515_measured_trace_collector.workload",
                       side_effect=lambda i, rounds: f"digest{i}"):
                collect(output, warmups=0, calibrations=2, holdouts=2,
                        rounds_override=1, source_kind="synthetic")
            result = evaluate(output / "catalog.csv", output / "holdout_traces.csv",
                              output / "provenance.json")
            self.assertEqual(result["run_count"], 2)
            self.assertEqual(result["source_kind"], "synthetic")

    def test_existing_evidence_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            marker = output / "marker.txt"
            marker.write_text("original", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                collect(output, rounds_override=1, source_kind="synthetic")
            self.assertEqual(marker.read_text(encoding="utf-8"), "original")

    def test_invalid_run_counts_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                collect(Path(temp) / "invalid", calibrations=1)
            with self.assertRaises(ValueError):
                collect(Path(temp) / "invalid", holdouts=1)

    def test_mocked_nondeterministic_task_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            calls = [0]
            def unstable(task_id, rounds):
                calls[0] += 1
                return str(calls[0])
            with patch("research.e515_measured_trace_collector.workload", side_effect=unstable), self.assertRaisesRegex(RuntimeError, "nondeterministic"):
                collect(Path(temp) / "pilot", warmups=1, calibrations=2,
                        holdouts=2, rounds_override=1, source_kind="synthetic")


if __name__ == "__main__":
    unittest.main()
