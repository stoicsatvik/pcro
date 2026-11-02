"""Deterministic E511 controls; no hidden evaluator or real latency data."""
import unittest

from research.e507_gaussian_copula import BUDGET, fixture, realized
from research.e511_heldout_tail_proxy import completes, evaluate, sign


class HeldoutTailProxyTests(unittest.TestCase):
    def test_completion_uses_same_inclusive_deadline_as_realized(self):
        rows = [(0, 10, 100), (1, 20, 300), (2, 30, 1)]
        factors = [1.0, 1.0, 1.0]
        self.assertTrue(completes(rows, [0, 1], factors))
        self.assertEqual(realized(rows, [0, 1], factors), 30)
        self.assertFalse(completes(rows, [0, 1, 2], factors))
        self.assertEqual(BUDGET, 400)

    def test_sign_proxy_handles_ties_without_claiming_success(self):
        self.assertEqual(sign(-0.01), -1)
        self.assertEqual(sign(0.0), 0)
        self.assertEqual(sign(0.01), 1)
        self.assertEqual(sign(1e-10), 0)

    def test_new_cohort_does_not_overlap_e507_training_cohort(self):
        self.assertNotEqual(fixture(1024), fixture(1023))
        self.assertGreater(1024, 1023)

    def test_repeated_small_heldout_experiment_is_deterministic(self):
        a = evaluate(start=1024, end=1024, draws=4)
        b = evaluate(start=1024, end=1024, draws=4)
        self.assertEqual(a, b)
        self.assertEqual(a["summary"]["gaussian"]["seed_count"], 1)
        self.assertEqual(a["summary"]["bernoulli"]["seed_count"], 1)

    def test_invalid_experiment_bounds_are_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(start=1025, end=1024)
        with self.assertRaises(ValueError):
            evaluate(start=1024, end=1024, draws=0)


if __name__ == "__main__":
    unittest.main()
