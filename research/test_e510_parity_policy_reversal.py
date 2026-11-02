"""E510: exact synthetic scheduling-policy reversal under pairwise-identical latency.

This is a three-task counterexample, not empirical replay evidence or a
validation of the E507 24-task scheduling policies.
"""

import itertools
import unittest
from collections import Counter
from fractions import Fraction

from research.test_e509_parity_copula import parity_states, prefix_overrun_probability


REWARD_PER_TASK = 10
MISS_PENALTY = 10
DEADLINE_MS = 300
NOMINAL_TASK_MS = 100
MAX_FACTOR = Fraction(13, 10)


def all_three_expected_utility(odd: bool) -> Fraction:
    """Two tasks always finish; third either pays reward or miss penalty.

    All factors lie in [0.7, 1.3), so two tasks take less than 260 ms.
    A successful third task yields 30; a failed third yields 20 - 10 = 10.
    """
    complete = 1 - prefix_overrun_probability(odd)
    return (2 * REWARD_PER_TASK - MISS_PENALTY) + (
        REWARD_PER_TASK + MISS_PENALTY
    ) * complete


def two_task_expected_utility() -> int:
    """Two-task policy always completes, independent of dependence model."""
    assert 2 * NOMINAL_TASK_MS * MAX_FACTOR < DEADLINE_MS
    return 2 * REWARD_PER_TASK


class ParityPolicyReversalTests(unittest.TestCase):
    def test_pairwise_bit_distributions_identical(self):
        for i, j in itertools.combinations(range(3), 2):
            even = Counter((s[i], s[j]) for s in parity_states(False))
            odd = Counter((s[i], s[j]) for s in parity_states(True))
            self.assertEqual(even, odd)
            self.assertEqual(set(even.values()), {1})

    def test_two_task_policy_always_completes(self):
        self.assertEqual(two_task_expected_utility(), 20)
        self.assertLess(2 * NOMINAL_TASK_MS * MAX_FACTOR, DEADLINE_MS)

    def test_exact_three_task_expected_utility(self):
        self.assertEqual(all_three_expected_utility(False), Fraction(35, 2))
        self.assertEqual(all_three_expected_utility(True), Fraction(45, 2))

    def test_policy_ranking_reverses_despite_identical_pairs(self):
        baseline = two_task_expected_utility()
        self.assertEqual(all_three_expected_utility(False) - baseline, Fraction(-5, 2))
        self.assertEqual(all_three_expected_utility(True) - baseline, Fraction(5, 2))
        # Independent factors complete with probability exactly 1/2.
        independent_utility = (2 * REWARD_PER_TASK - MISS_PENALTY) + (
            REWARD_PER_TASK + MISS_PENALTY
        ) * Fraction(1, 2)
        self.assertEqual(independent_utility, baseline)


if __name__ == "__main__":
    unittest.main()
