"""E507: fixed-marginal Gaussian copula stress test for synthetic replay scheduling.

No attack payloads, evaluator access, or third-party requests. Policies and fixture
follow frozen E487; seeds 896..1023 are a fresh synthetic cohort.
"""
import json
import math
import random
from statistics import mean

BUDGET = 400
PENALTY = 50
START, END = 896, 1023
DRAWS = 256
Q = (0.0, 0.25, 0.4, 0.5, 0.55, 0.6, 0.675649, 0.75, 1.0)
POLICIES = ('exact400', 'exact360', 'dp50', 'dp100', 'chance90')


def fixture(seed, n=24):
    s = (seed + 1) & 0xffffffff
    rows = []
    for i in range(n):
        s = (1664525 * s + 1013904223) & 0xffffffff
        reward = 5 + s % 96
        s = (1664525 * s + 1013904223) & 0xffffffff
        rows.append((i, reward, 10 + s % 111))
    return rows


def density_order(rows):
    return sorted(rows, key=lambda r: (-r[1] / r[2], r[0]))


def exact(rows, cap):
    dp = [(0, 0, ()) for _ in range(cap + 1)]
    for idx, reward, cost in rows:
        new = dp.copy()
        for b in range(cost, cap + 1):
            old = dp[b - cost]
            cand = (old[0] + reward, old[1] + cost, old[2] + (idx,))
            cur = new[b]
            if cand[0] > cur[0] or (cand[0] == cur[0] and cand[1] < cur[1]):
                new[b] = cand
        dp = new
    selected = set(dp[cap][2])
    return [r[0] for r in density_order(rows) if r[0] in selected]


def survival(cost):
    return 1 if cost == 0 else max(0.0, min(1.0, (BUDGET / cost - 0.7) / 0.6))


def optimize(rows, penalty=0, min_completion=0):
    limit = int(BUDGET / 0.7)
    dp = [(-math.inf, ()) for _ in range(limit + 1)]
    dp[0] = (0.0, ())
    for idx, reward, cost in density_order(rows):
        for c in range(limit, cost - 1, -1):
            old = dp[c - cost]
            if not math.isfinite(old[0]):
                continue
            value = old[0] + reward * survival(c)
            if value > dp[c][0] + 1e-10:
                dp[c] = (value, old[1] + (idx,))
    best = None
    for c, (value, ids) in enumerate(dp):
        if not math.isfinite(value) or survival(c) + 1e-12 < min_completion:
            continue
        u = value - penalty * (1 - survival(c))
        if best is None or u > best[0] + 1e-10:
            best = (u, ids)
    return list(best[1])


def policies(rows):
    return {'exact400': exact(rows, 400), 'exact360': exact(rows, 360),
            'dp50': optimize(rows, 50), 'dp100': optimize(rows, 100),
            'chance90': optimize(rows, 0, 0.9)}


def gaussian_factors(common, independent, target_uniform_corr):
    # For Gaussian copula with U=Phi(Z), Corr(U_i,U_j)=6/pi * asin(rho/2).
    # Latent rho=2*sin(pi*q/6) gives uniform Pearson corr q.
    rho = 0.0 if target_uniform_corr == 0 else (1.0 if target_uniform_corr == 1 else 2 * math.sin(math.pi * target_uniform_corr / 6))
    root = math.sqrt(max(0.0, 1 - rho))
    shared = math.sqrt(rho)
    return [0.7 + 0.6 * (0.5 * (1 + math.erf((shared * common + root * z) / math.sqrt(2))))
            for z in independent]


def realized(rows, ids, factors):
    cost = reward = 0.0
    for idx in ids:
        _, r, c = rows[idx]
        if cost + c * factors[idx] > BUDGET:
            return reward - PENALTY
        cost += c * factors[idx]
        reward += r
    return reward


def describe(values):
    avg = mean(values)
    se = math.sqrt(sum((v - avg) ** 2 for v in values) / ((len(values) - 1) * len(values)))
    return {'mean': round(avg, 6), 'seed_se': round(se, 6),
            'descriptive_95': [round(avg - 1.96 * se, 6), round(avg + 1.96 * se, 6)]}


def run():
    per_seed = []
    for seed in range(START, END + 1):
        rows = fixture(seed)
        selected = policies(rows)
        totals = {family: {str(q): {p: 0.0 for p in POLICIES} for q in Q}
                  for family in ('gaussian', 'bernoulli')}
        rng = random.Random(0xE5070000 ^ seed)
        for _ in range(DRAWS):
            common = rng.gauss(0, 1)
            independent = [rng.gauss(0, 1) for _ in rows]
            independent_factors = gaussian_factors(common, independent, 0.0)
            shared_factors = gaussian_factors(common, independent, 1.0)
            base = {p: realized(rows, selected[p], independent_factors) for p in POLICIES}
            shared = {p: realized(rows, selected[p], shared_factors) for p in POLICIES}
            for q in Q:
                key = str(q)
                factors = gaussian_factors(common, independent, q)
                for p in POLICIES:
                    totals['gaussian'][key][p] += realized(rows, selected[p], factors)
                    totals['bernoulli'][key][p] += (1 - q) * base[p] + q * shared[p]
        per_seed.append({family: {str(q): {p: totals[family][str(q)][p] / DRAWS
                                              for p in POLICIES} for q in Q}
                         for family in ('gaussian', 'bernoulli')})
    results = {}
    for p in POLICIES[1:]:
        results[p] = {}
        for family in ('gaussian', 'bernoulli'):
            results[p][family] = {
                str(q): describe([s[family][str(q)][p] - s[family][str(q)]['exact400']
                                  for s in per_seed]) for q in Q
            }
        results[p]['gaussian_minus_bernoulli'] = {
            str(q): describe([
                (s['gaussian'][str(q)][p] - s['gaussian'][str(q)]['exact400']) -
                (s['bernoulli'][str(q)][p] - s['bernoulli'][str(q)]['exact400'])
                for s in per_seed]) for q in Q
        }
    return {'experiment': 'E507_MATCHED_MARGINAL_COPULA_FAMILY',
            'cohort': [START, END], 'draws_per_seed': DRAWS, 'policies': POLICIES,
            'q_is_target_uniform_Pearson_correlation': Q,
            'results': results,
            'claim': 'Synthetic matched-marginal copula-family sensitivity only, no measured latency or real replay utility',
            'limits': 'Both families have U[0.7,1.3] marginals and equal pairwise Pearson correlation q analytically; deterministic finite Monte Carlo, no external data'}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
