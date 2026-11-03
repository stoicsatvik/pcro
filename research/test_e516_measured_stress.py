"""E516 frozen-protocol controls; mocked timing is not empirical validation."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.e516_measured_stress import (
    N_TASKS,
    collect,
    policy_gate,
    scaled_rounds,
)


class StressProtocolTests(unittest.TestCase):
    def test_multiplier_frozen_exact(self):
        self.assertEqual(scaled_rounds(0), 12000)
        self.assertEqual(scaled_rounds(23), 87900)

    def test_predeclared_pilot_gate_and_scaled_divergence(self):
        pilot = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                 15, 16, 17, 18, 19, 20, 21, 21, 23, 23, 24, 25]
        self.assertFalse(policy_gate(pilot)["divergent"])
        scaled = [max(1, round(v * 1.5)) for v in pilot]
        self.assertTrue(policy_gate(scaled)["divergent"])

    def test_invalid_calibration_gate_rejected(self):
        for values in ([1] * 23, [1] * 23 + [0], [1] * 23 + [1.5]):
            with self.subTest(values=values[-1]), self.assertRaises(ValueError):
                policy_gate(values)

    def test_complete_mocked_traces_and_pre_holdout_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "new"
            counter = iter(range(0, 10**12, 1_000_000))
            with patch("research.e516_measured_stress.workload",
                       side_effect=lambda task_id, rounds: f"digest-{task_id}"), patch(
                       "research.e516_measured_stress.time.perf_counter_ns",
                       side_effect=lambda: next(counter)):
                result = collect(output, warmups=0, calibrations=2, holdouts=2,
                                 source_kind="synthetic")
            meta = result["provenance"]
            with (output / "holdout_traces.csv").open(newline="", encoding="utf-8") as stream:
                traces = list(csv.DictReader(stream))
            self.assertEqual(len(traces), 2 * N_TASKS)
            self.assertEqual(result["replay"]["run_count"], 2)
            self.assertFalse(meta["pre_holdout_gate"]["divergent"])
            self.assertEqual(meta["pre_holdout_gate"]["nominal_total_ms"], 24)
            self.assertEqual(meta["trace_sha256"], hashlib.sha256(
                (output / "holdout_traces.csv").read_bytes()).hexdigest())
            self.assertEqual(json.loads((output / "provenance.json").read_text())
                             ["catalog_sha256"], meta["catalog_sha256"])

    def test_existing_evidence_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "marker.txt"
            marker.write_text("untouched", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                collect(temp, source_kind="synthetic")
            self.assertEqual(marker.read_text(encoding="utf-8"), "untouched")

    def test_invalid_run_counts_and_kind(self):
        with tempfile.TemporaryDirectory() as temp:
            for kwargs in ({"calibrations": 1}, {"holdouts": 1},
                           {"warmups": -1}, {"holdouts": 2.5},
                           {"source_kind": "unknown"}):
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    collect(Path(temp) / "bad", **kwargs)

    def test_nondeterministic_output_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            calls = iter(range(10000))
            with patch("research.e516_measured_stress.workload",
                       side_effect=lambda task_id, rounds: str(next(calls))), self.assertRaisesRegex(
                       RuntimeError, "nondeterministic"):
                collect(Path(temp) / "bad", warmups=1, calibrations=2,
                        holdouts=2, source_kind="synthetic")


if __name__ == "__main__":
    unittest.main()
