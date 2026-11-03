"""E512 deterministic controls; not a measured replay benchmark."""
import random
import unittest

from research.e507_gaussian_copula import BUDGET, PENALTY, realized
from research.e512_reward_prefix_proxy import (
    DIAGNOSTIC_STREAM,
    END,
    OUTCOME_STREAM,
    START,
    _scenarios,
    completed_prefix_reward,
    evaluate,
)


class IndependentRewardPrefixTests(unittest.TestCase):
    def test_prefix_reward_stops_on_first_failure(self):
        rows = [(0, 10, 200), (1, 20, 200), (2, 30, 1)]
        factors = [1.0, 1.1, 1.0]
        self.assertEqual(completed_prefix_reward(rows, [0, 1, 2], factors), 10)
        self.assertEqual(realized(rows, [0, 1, 2], factors), 10 - PENALTY)

    def test_exact_budget_is_inclusive(self):
        rows = [(0, 10, 100), (1, 20, 300), (2, 30, 1)]
        factors = [1.0, 1.0, 1.0]
        self.assertEqual(BUDGET, 400)
        self.assertEqual(completed_prefix_reward(rows, [0, 1], factors), 30)
        self.assertEqual(completed_prefix_reward(rows, [0, 1, 2], factors), 30)
        self.assertEqual(realized(rows, [0, 1], factors), 30)
        self.assertEqual(realized(rows, [0, 1, 2], factors), 30 - PENALTY)

    def test_empty_selection_has_zero_reward(self):
        self.assertEqual(completed_prefix_reward([(0, 10, 1)], [], [1.0]), 0)

    def test_diagnostic_and_outcome_random_streams_are_distinct(self):
        self.assertNotEqual(DIAGNOSTIC_STREAM, OUTCOME_STREAM)
        a = next(_scenarios(random.Random(DIAGNOSTIC_STREAM ^ START), 3, 1))
        b = next(_scenarios(random.Random(OUTCOME_STREAM ^ START), 3, 1))
        self.assertNotEqual(a, b)
        self.assertAlmostEqual(sum(w for w, _ in a["bernoulli"]), 1.0)

    def test_new_cohort_does_not_overlap_e511(self):
        self.assertEqual((START, END), (1056, 1087))
        self.assertGreater(START, 1055)

    def test_small_cohort_reproducible_and_both_proxies_reported(self):
        a = evaluate(start=START, end=START, draws=4)
        self.assertEqual(a, evaluate(start=START, end=START, draws=4))
        for family in ("gaussian", "bernoulli"):
            self.assertEqual(a["summary"][family]["seed_count"], 1)
            self.assertIn("reward_prefix", a["summary"][family])
            self.assertIn("completion", a["summary"][family])

    def test_invalid_bounds_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(start=START + 1, end=START)
        with self.assertRaises(ValueError):
            evaluate(start=START, end=START, draws=0)


if __name__ == "__main__":
    unittest.main()
