"""E513 synthetic controls. No empirical latency traces are bundled or claimed."""
import csv
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path

from research.e507_gaussian_copula import fixture, policies, realized
from research.e513_trace_replay import (
    N_TASKS,
    check_provenance,
    evaluate,
    load_catalog,
    load_complete_runs,
)


class TraceGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = self.root / "catalog.csv"
        self.traces = self.root / "traces.csv"
        self.provenance = self.root / "provenance.json"
        self.rows = fixture(2026)
        self.write_catalog()
        self.write_traces()
        self.write_provenance()

    def write_catalog(self, rows=None):
        with self.catalog.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("task_id", "reward", "nominal_ms"))
            writer.writerows(rows if rows is not None else self.rows)

    def write_traces(self, entries=None):
        if entries is None:
            entries = [
                (run_id, task_id, nominal * factor)
                for run_id, factor in (("r1", 1.0), ("r2", 1.2))
                for task_id, _, nominal in self.rows
            ]
        with self.traces.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("run_id", "task_id", "duration_ms"))
            writer.writerows(entries)

    def write_provenance(self, **overrides):
        metadata = {
            "dataset_id": "synthetic-test-fixture",
            "source_kind": "synthetic",
            "time_unit": "ms",
            "trace_sha256": hashlib.sha256(self.traces.read_bytes()).hexdigest(),
            "catalog_sha256": hashlib.sha256(self.catalog.read_bytes()).hexdigest(),
        }
        metadata.update(overrides)
        self.provenance.write_text(json.dumps(metadata), encoding="utf-8")

    def test_complete_paired_replay_matches_frozen_realized(self):
        result = evaluate(self.catalog, self.traces, self.provenance)
        self.assertEqual(result["run_count"], 2)
        self.assertEqual(result["task_count"], N_TASKS)
        self.assertEqual(result["source_kind"], "synthetic")
        chosen = policies(self.rows)
        for item, factor in zip(result["per_run"], (1.0, 1.2)):
            factors = [factor] * N_TASKS
            a = realized(self.rows, chosen["dp50"], factors)
            b = realized(self.rows, chosen["exact400"], factors)
            self.assertEqual((item["dp50"], item["exact400"], item["gap"]), (a, b, a - b))
        self.assertTrue(math.isfinite(result["descriptive_paired_se"]))

    def test_missing_task_rejected_as_censored(self):
        self.write_traces([
            (run_id, task_id, nominal)
            for run_id in ("r1", "r2")
            for task_id, _, nominal in self.rows
            if not (run_id == "r2" and task_id == 23)
        ])
        with self.assertRaisesRegex(ValueError, "censored"):
            load_complete_runs(self.traces)

    def test_duplicate_task_rejected(self):
        entries = [
            (run_id, task_id, nominal)
            for run_id in ("r1", "r2")
            for task_id, _, nominal in self.rows
        ]
        entries.append(entries[0])
        self.write_traces(entries)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            load_complete_runs(self.traces)

    def test_nonfinite_and_nonpositive_durations_rejected(self):
        for invalid in ("NaN", "inf", "-1", "0"):
            with self.subTest(invalid=invalid):
                entries = [
                    (run_id, task_id, invalid if run_id == "r1" and task_id == 0 else nominal)
                    for run_id in ("r1", "r2")
                    for task_id, _, nominal in self.rows
                ]
                self.write_traces(entries)
                with self.assertRaisesRegex(ValueError, "duration_ms"):
                    load_complete_runs(self.traces)

    def test_tampered_trace_digest_rejected(self):
        self.traces.write_text(self.traces.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            check_provenance(self.provenance, self.traces, self.catalog)

    def test_measured_claim_requires_protocol_but_is_not_authenticated(self):
        self.write_provenance(source_kind="measured")
        with self.assertRaisesRegex(ValueError, "collection_protocol"):
            check_provenance(self.provenance, self.traces, self.catalog)
        self.write_provenance(source_kind="measured", collection_protocol="self-reported benchmark")
        result = evaluate(self.catalog, self.traces, self.provenance)
        self.assertEqual(result["source_kind"], "measured")
        self.assertIn("not authenticated", result["limitations"])

    def test_wrong_unit_rejected(self):
        self.write_provenance(time_unit="seconds")
        with self.assertRaisesRegex(ValueError, "time_unit"):
            check_provenance(self.provenance, self.traces, self.catalog)

    def test_catalog_missing_or_duplicate_ids_rejected(self):
        self.write_catalog(self.rows[:-1])
        with self.assertRaisesRegex(ValueError, "exactly 24"):
            load_catalog(self.catalog)
        self.write_catalog(self.rows[:-1] + [self.rows[0]])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            load_catalog(self.catalog)

    def test_extra_csv_column_rejected(self):
        self.traces.write_text(
            "run_id,task_id,duration_ms,secret\nr1,0,10,unexpected\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "columns"):
            load_complete_runs(self.traces)

    def test_single_run_cannot_claim_standard_error(self):
        self.write_traces([
            ("r1", task_id, nominal) for task_id, _, nominal in self.rows
        ])
        with self.assertRaisesRegex(ValueError, "two complete runs"):
            load_complete_runs(self.traces)


    def test_catalog_tamper_rejected_with_unchanged_trace(self):
        original_trace_digest = hashlib.sha256(self.traces.read_bytes()).hexdigest()
        changed = list(self.rows)
        task_id, reward, nominal = changed[0]
        changed[0] = (task_id, reward + 1, nominal)
        self.write_catalog(changed)
        self.assertEqual(hashlib.sha256(self.traces.read_bytes()).hexdigest(), original_trace_digest)
        with self.assertRaisesRegex(ValueError, "catalog SHA256 mismatch"):
            evaluate(self.catalog, self.traces, self.provenance)

    def test_missing_catalog_digest_rejected(self):
        self.write_provenance(catalog_sha256=None)
        with self.assertRaisesRegex(ValueError, "catalog SHA256 mismatch"):
            evaluate(self.catalog, self.traces, self.provenance)

    def test_coherent_catalog_and_metadata_rewrite_still_passes(self):
        original_digest = hashlib.sha256(self.catalog.read_bytes()).hexdigest()
        changed = list(self.rows)
        task_id, reward, nominal = changed[0]
        changed[0] = (task_id, reward + 1, nominal)
        self.write_catalog(changed)
        self.write_provenance()
        result = evaluate(self.catalog, self.traces, self.provenance)
        self.assertNotEqual(result["catalog_sha256"], original_digest)
        self.assertEqual(result["source_kind"], "synthetic")
        self.assertIn("not authenticated", result["limitations"])


if __name__ == "__main__":
    unittest.main()
