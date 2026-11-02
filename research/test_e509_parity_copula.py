"""E509: exact higher-order dependence counterexample for three synthetic tasks.

Both parity copulas have identical U[0.7, 1.3] one-dimensional marginals
and identical *pairwise joint distributions*, not merely Pearson correlation.
They differ in three-way tail events and 300 ms prefix completion.
"""

import itertools
import unittest
from collections import Counter
from fractions import Fraction


def parity_states(odd: bool):
    """Four equiprobable binary triples, with even/odd XOR parity."""
    return tuple((a, b, a ^ b ^ int(odd)) for a, b in itertools.product((0, 1), repeat=2))


def prefix_overrun_probability(odd: bool):
    """Exact P(sum of three 100-ms task factors > 3), with uniform jitter.

    For each bit b, F = 0.7 + 0.3*(b + U), U iid U[0,1).
    For S = U1+U2+U3, P(S > 3-k) for k high bits is tabulated
    from the exact Irwin-Hall(3) distribution, not Monte Carlo.
    """
    tail_by_high_count = (
        Fraction(0), Fraction(1, 6), Fraction(5, 6), Fraction(1)
    )
    return sum(
        (tail_by_high_count[sum(state)] for state in parity_states(odd)),
        Fraction(0),
    ) / 4


class HigherOrderDependenceTests(unittest.TestCase):
    def test_each_bit_and_pair_is_independent_fair(self):
        for odd in (False, True):
            states = parity_states(odd)
            self.assertEqual(len(set(states)), 4)
            for i in range(3):
                self.assertEqual(Counter(s[i] for s in states), {0: 2, 1: 2})
            for i, j in itertools.combinations(range(3), 2):
                self.assertEqual(
                    Counter((s[i], s[j]) for s in states),
                    {(0, 0): 1, (0, 1): 1, (1, 0): 1, (1, 1): 1},
                )

    def test_three_way_tail_is_not_determined_by_pairs(self):
        self.assertEqual(sum(s == (1, 1, 1) for s in parity_states(False)), 0)
        self.assertEqual(sum(s == (1, 1, 1) for s in parity_states(True)), 1)
        # Each pair exceeds factor 1.0 with probability exactly 1/4.
        # Triple exceedance differs: 0 versus 1/4.

    def test_exact_three_task_completion_probability_differs(self):
        self.assertEqual(prefix_overrun_probability(False), Fraction(5, 8))
        self.assertEqual(prefix_overrun_probability(True), Fraction(3, 8))
        self.assertEqual(1 - prefix_overrun_probability(False), Fraction(3, 8))
        self.assertEqual(1 - prefix_overrun_probability(True), Fraction(5, 8))

    def test_independent_uniform_baseline_is_half_overrun(self):
        # Eight equiprobable independent bit triples, same jitter law.
        tails = (Fraction(0), Fraction(1, 6), Fraction(5, 6), Fraction(1))
        states = itertools.product((0, 1), repeat=3)
        overrun = sum((tails[sum(s)] for s in states), Fraction(0)) / 8
        self.assertEqual(overrun, Fraction(1, 2))


if __name__ == "__main__":
    unittest.main()
