"""E287: complete exact k-wise independence vs eight-way tail frontier.

Abstract exchangeable Bernoulli outcomes, not observed security/replay outcomes.
Every LP vertex is enumerated with exact Fraction arithmetic. No optimizer
tolerance, random seed, attack implementation, or hidden benchmark access.
"""
from __future__ import annotations

import json
from fractions import Fraction
from itertools import combinations
from math import comb

N = 8
EXPECTED_MAX = {
    1: Fraction(1, 2),
    2: Fraction(1, 10),
    3: Fraction(1, 16),
    4: Fraction(1, 40),
    5: Fraction(1, 72),
    6: Fraction(1, 112),
    7: Fraction(1, 128),
    8: Fraction(1, 256),
}
EXPECTED_VERTICES = {1: 24, 2: 31, 3: 35, 4: 25, 5: 25, 6: 18, 7: 9, 8: 1}


def falling(n: int, order: int) -> int:
    out = 1
    for j in range(order):
        out *= n - j
    return out


def moment_target(order: int) -> Fraction:
    return Fraction(falling(N, order), 2**order)


def moments(law: dict[int, Fraction], order: int) -> tuple[Fraction, ...]:
    return tuple(
        sum((p * falling(n, j) for n, p in law.items()), Fraction())
        for j in range(order + 1)
    )


def solve_support(support: tuple[int, ...], order: int) -> dict[int, Fraction] | None:
    """Solve the full-rank falling-factorial Vandermonde system exactly."""
    size = order + 1
    if len(support) != size or len(set(support)) != size:
        raise ValueError("Expected distinct support points of full basis size")
    rows = [
        [Fraction(falling(n, j)) for n in support] + [moment_target(j)]
        for j in range(size)
    ]
    for col in range(size):
        pivot = next((i for i in range(col, size) if rows[i][col]), None)
        if pivot is None:
            raise AssertionError("Distinct-support moment matrix is singular")
        rows[col], rows[pivot] = rows[pivot], rows[col]
        scale = rows[col][col]
        rows[col] = [x / scale for x in rows[col]]
        for i in range(size):
            if i != col:
                factor = rows[i][col]
                rows[i] = [x - factor * y for x, y in zip(rows[i], rows[col])]
    weights = [row[-1] for row in rows]
    if any(p < 0 for p in weights):
        return None
    law = dict(zip(support, weights))
    assert moments(law, order) == tuple(moment_target(j) for j in range(size))
    return law


def extrema(order: int) -> dict:
    if not 1 <= order <= N:
        raise ValueError("Independence order must be in [1, 8]")
    feasible = []
    for support in combinations(range(N + 1), order + 1):
        law = solve_support(support, order)
        if law is not None:
            feasible.append(law)
    if not feasible:
        raise AssertionError("No feasible exchangeable laws")
    smallest = min(feasible, key=lambda law: law.get(0, Fraction()))
    largest = max(feasible, key=lambda law: law.get(0, Fraction()))
    return {
        "order": order,
        "bases_enumerated": comb(N + 1, order + 1),
        "feasible_bases": len(feasible),
        "lower": smallest.get(0, Fraction()),
        "upper": largest.get(0, Fraction()),
        "lower_law": smallest,
        "upper_law": largest,
    }


def verify_kwise(law: dict[int, Fraction], order: int) -> None:
    """Check every possible j-bit success count pattern, j <= order."""
    assert sum(law.values(), Fraction()) == 1
    assert all(p >= 0 for p in law.values())
    for j in range(1, order + 1):
        for successes in range(j + 1):
            probability = sum(
                (
                    p * Fraction(comb(N - j, n - successes), comb(N, n))
                    for n, p in law.items()
                    if 0 <= n - successes <= N - j
                ),
                Fraction(),
            )
            assert probability == Fraction(1, 2**j), (order, j, successes)


def encode_law(law: dict[int, Fraction]) -> dict[str, str]:
    return {str(n): str(p) for n, p in sorted(law.items()) if p}


def audit() -> dict:
    independent = Fraction(1, 2**N)
    rows = []
    for order in range(1, N + 1):
        result = extrema(order)
        assert result["upper"] == EXPECTED_MAX[order]
        assert result["feasible_bases"] == EXPECTED_VERTICES[order]
        assert result["lower"] == (independent if order == N else 0)
        verify_kwise(result["lower_law"], order)
        verify_kwise(result["upper_law"], order)
        rows.append({
            "k": order,
            "basis_count": result["bases_enumerated"],
            "feasible_bases": result["feasible_bases"],
            "all_fail_lower": str(result["lower"]),
            "all_fail_upper": str(result["upper"]),
            "worst_case_multiple_of_full_independence": str(
                result["upper"] / independent
            ),
            "attaining_upper_count_law": encode_law(result["upper_law"]),
            "attaining_lower_count_law": encode_law(result["lower_law"]),
        })
    return {
        "schema": "pcro/e287/kwise-tail-identifiability-frontier/v1",
        "n": N,
        "marginal_success_probability": "1/2",
        "full_independence_all_fail": str(independent),
        "independence_orders": rows,
        "proof": (
            "For each k, exchangeable count laws satisfy k+1 independent "
            "factorial-moment equalities and nonnegative probabilities. "
            "Every vertex of this bounded polytope has at most k+1 "
            "nonzero count masses; enumerate every (k+1)-point basis "
            "and solve with exact rational Gaussian elimination. "
            "Linear all-fail probability attains its extrema at vertices."
        ),
        "claim": (
            "Exact sharp bounds for exchangeable n=8 p=1/2 k-wise "
            "independent abstract outcomes; not empirical replay risk."
        ),
        "limitations": [
            "Exchangeability and p=1/2 are stipulated mathematical assumptions.",
            "No observed joint replay corpus, failure labels, or prospective test.",
            "k-wise independence is an assumption, not evidence of actual independence.",
            "No third-party security testing, hidden evaluator or attacks.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
