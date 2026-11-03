"""E517 deterministic controls; the E516 data are reused, not recollected."""
import json
import tempfile
import unittest
from pathlib import Path

from research.e517_budget_sensitivity import replay_at_budget, sweep

ROOT = Path(__file__).resolve().parents[1] / "research"
RESULTS = ROOT / "results"
CATALOG = RESULTS / "e516_cpu_stress_catalog.csv"
TRACES = RESULTS / "e516_cpu_stress_holdout_traces.csv"
PROVENANCE = RESULTS / "e516_cpu_stress_provenance.json"


class BudgetSensitivityTests(unittest.TestCase):
    def test_strict_deadline_and_penalty_semantics(self):
        rows = [(0, 10, 100), (1, 20, 100)]
        durations = [100.0, 101.0]
        self.assertEqual(replay_at_budget(rows, [0, 1], durations, 201), 30)
        self.assertEqual(replay_at_budget(rows, [0, 1], durations, 200), -40)
        self.assertEqual(replay_at_budget(rows, [0, 1], durations, 200, 0), 10)

    def test_reject_invalid_budget_and_penalty(self):
        for budget in (0, -1, 400.0, True):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                replay_at_budget([(0, 1, 1)], [0], [1.0], budget)
        for penalty in (-1, 1.5, True):
            with self.subTest(penalty=penalty), self.assertRaises(ValueError):
                replay_at_budget([(0, 1, 1)], [0], [1.0], 400, penalty)

    def test_exact_e516_400ms_replay_and_sign_reversal(self):
        result = sweep(CATALOG, TRACES, PROVENANCE)
        self.assertEqual(result["run_count"], 6)
        self.assertEqual(result["mean_gap_at_400"], -200 / 6)
        self.assertEqual(result["points"][50]["gaps"], [0, -50, -50, 0, -50, -50])
        self.assertGreater(result["mean_gap_at_450"], 0)
        self.assertEqual(result["points"][100]["gaps"], [-19, -3, -3, -19, -3, 55])
        self.assertEqual(len(result["points"]), 151)

    def test_mismatched_gate_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            meta = json.loads(PROVENANCE.read_text(encoding="utf-8"))
            meta["pre_holdout_gate"]["dp50"] = []
            path = Path(temp) / "forged.json"
            path.write_text(json.dumps(meta), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "policy gate"):
                sweep(CATALOG, TRACES, path)

    def test_source_kind_cannot_be_relabelled_as_synthetic(self):
        with tempfile.TemporaryDirectory() as temp:
            meta = json.loads(PROVENANCE.read_text(encoding="utf-8"))
            meta["source_kind"] = "synthetic"
            path = Path(temp) / "synthetic.json"
            path.write_text(json.dumps(meta), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "frozen E516 measured"):
                sweep(CATALOG, TRACES, path)


if __name__ == "__main__":
    unittest.main()
