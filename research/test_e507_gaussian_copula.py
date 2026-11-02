import math
import random
import unittest
from e507_gaussian_copula import (
    density_order,
    exact,
    fixture,
    gaussian_factors,
    optimize,
    run,
    survival,
)


class GaussianCopulaTests(unittest.TestCase):
    def test_fixture_deterministic_and_bounded(self):
        self.assertEqual(fixture(768), fixture(768))
        self.assertEqual(len(fixture(768)), 24)
        self.assertTrue(all(5 <= r <= 100 and 10 <= c <= 120 for _, r, c in fixture(768)))

    def test_exact_knapsack_against_exhaustive_oracle(self):
        rows = fixture(768, 8)
        ids = exact(rows, 400)
        reward = sum(rows[i][1] for i in ids)
        brute = max(sum(rows[i][1] for i in range(8) if mask & (1 << i))
                    for mask in range(256)
                    if sum(rows[i][2] for i in range(8) if mask & (1 << i)) <= 400)
        self.assertEqual(reward, brute)

    def test_dp_objective_against_exhaustive_oracle(self):
        for seed in range(3):
            rows = fixture(seed, 8)
            order = density_order(rows)
            for penalty in (0, 50, 100):
                best = -math.inf
                for mask in range(256):
                    chosen = [row for i, row in enumerate(order) if mask & (1 << i)]
                    cost = value = 0
                    for _, reward, c in chosen:
                        cost += c
                        value += reward * survival(cost)
                    best = max(best, value - penalty * (1 - survival(cost)))
                selected = optimize(rows, penalty)
                selected_rows = [r for r in order if r[0] in selected]
                cost = value = 0
                for _, reward, c in selected_rows:
                    cost += c
                    value += reward * survival(cost)
                self.assertAlmostEqual(value - penalty * (1 - survival(cost)), best)

    def test_fixed_uniform_marginal_correlation_parameterization(self):
        for q in (0, 0.25, 0.5, 0.55, 0.75, 1):
            rho = 2 * math.sin(math.pi * q / 6)
            self.assertAlmostEqual(6 / math.pi * math.asin(rho / 2), q)

    def test_shared_and_independent_endpoints(self):
        independent = [1.5, -0.5, 0.3]
        self.assertEqual(len(set(gaussian_factors(0.4, independent, 1))), 1)
        a = gaussian_factors(0.4, independent, 0)
        b = gaussian_factors(-1.7, independent, 0)
        self.assertEqual(a, b)
        self.assertTrue(all(0.7 < x < 1.3 for x in a))

    def test_empirical_correlation_under_q_half(self):
        rng = random.Random(507)
        n = 10000
        a, b = [], []
        for _ in range(n):
            v = gaussian_factors(rng.gauss(0, 1), [rng.gauss(0, 1), rng.gauss(0, 1)], 0.5)
            a.append(v[0]); b.append(v[1])
        ma = sum(a) / n; mb = sum(b) / n
        cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        va = sum((x - ma) ** 2 for x in a)
        vb = sum((y - mb) ** 2 for y in b)
        self.assertAlmostEqual(cov / math.sqrt(va * vb), 0.5, delta=0.025)

    def test_new_cohort_copula_family_changes_policy_rank(self):
        result = run()['results']['dp50']
        self.assertGreater(result['gaussian']['0.55']['mean'], 0)
        self.assertLess(result['bernoulli']['0.55']['mean'], 0)
        self.assertGreater(result['gaussian_minus_bernoulli']['0.55']['mean'], 3)
        self.assertAlmostEqual(result['gaussian_minus_bernoulli']['0.0']['mean'], 0)
        self.assertAlmostEqual(result['gaussian_minus_bernoulli']['1.0']['mean'], 0)


if __name__ == '__main__':
    unittest.main()
