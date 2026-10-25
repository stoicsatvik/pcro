"""E276: exact triplewise-independent, eight-way catastrophic-tail ambiguity.

Abstract exchangeable Bernoulli outcomes only; no real replay, exploit traces,
hidden evaluation, unauthorized security testing, or empirical risk estimates.
"""
from __future__ import annotations

import json
import math
from fractions import Fraction
from itertools import combinations

N = 8
MOMENTS = (Fraction(1), Fraction(4), Fraction(14), Fraction(42))
# Distribution of K = number of successes; conditionally uniform K-subsets.
ZERO_TAIL = {1: Fraction(1, 15), 3: Fraction(1, 3),
             4: Fraction(1, 3), 6: Fraction(4, 15)}
MAX_TAIL = {0: Fraction(1, 16), 4: Fraction(7, 8), 8: Fraction(1, 16)}
INDEPENDENT = {k: Fraction(math.comb(N, k), 2**N) for k in range(N + 1)}


def falling(k: int, order: int) -> int:
    result = 1
    for j in range(order):
        result *= k - j
    return result


def factorial_moments(law: dict[int, Fraction]) -> tuple[Fraction, ...]:
    return tuple(sum((p * falling(k, order) for k, p in law.items()), Fraction())
                 for order in range(4))


def validate(law: dict[int, Fraction]) -> None:
    if not law or any(not isinstance(k, int) or not 0 <= k <= N
                      or not isinstance(p, Fraction) or p < 0
                      for k, p in law.items()):
        raise ValueError("Invalid exact exchangeable count law")
    if factorial_moments(law) != MOMENTS:
        raise ValueError("First three factorial moments are not frozen")


def dual_upper(k: int) -> Fraction:
    """For k in [0,8], 1[k=0] <= (k-4)^2*(8-k)/128."""
    if not 0 <= k <= N:
        raise ValueError("Count outside [0,8]")
    return Fraction((k - 4) ** 2 * (8 - k), 128)


def solve_four_support(support: tuple[int, int, int, int]) -> dict[int, Fraction] | None:
    """Exact Gaussian elimination for four factorial-moment equalities."""
    rows = [[Fraction(falling(k, order)) for k in support] + [MOMENTS[order]]
            for order in range(4)]
    for col in range(4):
        pivot = next((r for r in range(col, 4) if rows[r][col]), None)
        if pivot is None:
            return None
        rows[col], rows[pivot] = rows[pivot], rows[col]
        scale = rows[col][col]
        rows[col] = [x / scale for x in rows[col]]
        for r in range(4):
            if r != col:
                factor = rows[r][col]
                rows[r] = [x - factor * y for x, y in zip(rows[r], rows[col])]
    weights = [row[4] for row in rows]
    if any(weight < 0 for weight in weights):
        return None
    return dict(zip(support, weights))


def vertex_extrema() -> tuple[Fraction, Fraction, int]:
    """Every vertex of this four-equality simplex has <=4 support points."""
    feasible = []
    for support in combinations(range(N + 1), 4):
        law = solve_four_support(support)
        if law is not None:
            validate(law)
            feasible.append(law.get(0, Fraction()))
    if not feasible:
        raise AssertionError("No feasible vertices")
    return min(feasible), max(feasible), len(feasible)


def full_joint(law: dict[int, Fraction]) -> dict[int, Fraction]:
    """All 256 exact outcome probabilities, via uniform subsets given K."""
    validate(law)
    return {mask: law.get(mask.bit_count(), Fraction())
            / math.comb(N, mask.bit_count()) for mask in range(1 << N)}


def verify_every_triple(law: dict[int, Fraction]) -> None:
    joint = full_joint(law)
    assert sum(joint.values(), Fraction()) == 1
    for triple in combinations(range(N), 3):
        for pattern in range(8):
            probability = sum(
                (p for mask, p in joint.items()
                 if all(bool(mask & (1 << index)) == bool(pattern & (1 << bit))
                        for bit, index in enumerate(triple))),
                Fraction(),
            )
            assert probability == Fraction(1, 8)


def audit() -> dict:
    for law in (ZERO_TAIL, MAX_TAIL, INDEPENDENT):
        validate(law)
        verify_every_triple(law)
    assert all(dual_upper(k) >= int(k == 0) for k in range(N + 1))
    assert all(sum((p * dual_upper(k) for k, p in law.items()), Fraction())
               == Fraction(1, 16) for law in (ZERO_TAIL, MAX_TAIL, INDEPENDENT))
    lower, upper, vertices = vertex_extrema()
    assert (lower, upper, vertices) == (Fraction(), Fraction(1, 16), 35)
    assert MAX_TAIL[0] == upper
    assert INDEPENDENT[0] == Fraction(1, 256)
    return {
        "schema": "pcro/e276/triplewise-tail-nonidentifiability/v1",
        "candidate_count": N,
        "triple_count": math.comb(N, 3),
        "joint_triple_patterns_checked_per_law": math.comb(N, 3) * 8,
        "first_three_factorial_moments": [str(x) for x in MOMENTS],
        "triplewise_independence": "all 56 triples have 8 patterns of exact probability 1/8",
        "exact_all_fail_bounds": [str(lower), str(upper)],
        "four_support_vertices_checked": vertices,
        "independent_all_fail": str(INDEPENDENT[0]),
        "max_to_independent_ratio": str(upper / INDEPENDENT[0]),
        "zero_tail_count_law": {str(k): str(v) for k, v in ZERO_TAIL.items()},
        "max_tail_count_law": {str(k): str(v) for k, v in MAX_TAIL.items()},
        "dual_certificate": "1[K=0] <= (K-4)^2*(8-K)/128 for K=0..8",
        "claim": "Triplewise independence still cannot identify eight-way all-fail risk (exact abstract model)",
        "limitations": [
            "No observed replay-family joint outcomes or empirical catastrophic risk",
            "Exchangeability and fixed p=1/2 are mathematical assumptions",
            "Triplewise independence does not imply eight-way independence",
            "No attacks, third-party access or hidden evaluation",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
