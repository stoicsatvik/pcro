"""E260: exact pairwise-independent replay-count tail non-identifiability.

Abstract exchangeable Bernoulli outcomes only. No exploit traces, targets,
hidden evaluators, unauthorized testing, or empirical replay observations.
"""
from __future__ import annotations

import json
import math
from fractions import Fraction
from itertools import combinations

N = 8
TARGET_MEAN = Fraction(4)
TARGET_FACTORIAL_SECOND = Fraction(14)
LOW_TAIL_MASS = Fraction(1, 10)

# All three laws have E[K]=4 and E[K(K-1)]=14, hence eight marginal
# success probabilities of 1/2 and all 28 pairwise correlations of zero.
ZERO_TAIL = {2: Fraction(1, 3), 5: Fraction(2, 3)}
MAX_TAIL = {0: Fraction(1, 10), 4: Fraction(1, 2), 5: Fraction(2, 5)}
INDEPENDENT = {k: Fraction(math.comb(N, k), 2**N) for k in range(N + 1)}


def moments(pmf: dict[int, Fraction]) -> tuple[Fraction, Fraction, Fraction]:
    """Total mass, expected successes, and second factorial moment."""
    return (
        sum(pmf.values(), Fraction()),
        sum((k * p for k, p in pmf.items()), Fraction()),
        sum((k * (k - 1) * p for k, p in pmf.items()), Fraction()),
    )


def selected_success_probability(pmf: dict[int, Fraction], count: int) -> Fraction:
    """Probability fixed distinct candidates all succeed under exchangeability."""
    if not 0 <= count <= N:
        raise ValueError("count must be in [0,8]")
    return sum(
        (
            p * Fraction(math.comb(N - count, k - count), math.comb(N, k))
            for k, p in pmf.items() if k >= count
        ),
        Fraction(),
    )


def validate(pmf: dict[int, Fraction]) -> None:
    if not pmf or any(
        not isinstance(k, int) or not 0 <= k <= N
        or not isinstance(p, Fraction) or p < 0
        for k, p in pmf.items()
    ):
        raise ValueError("invalid exact count law")
    if moments(pmf) != (Fraction(1), TARGET_MEAN, TARGET_FACTORIAL_SECOND):
        raise ValueError("count law violates frozen first/pairwise moments")
    if selected_success_probability(pmf, 1) != Fraction(1, 2):
        raise AssertionError("marginal mismatch")
    if selected_success_probability(pmf, 2) != Fraction(1, 4):
        raise AssertionError("pairwise mismatch")


def lower_decile(pmf: dict[int, Fraction]) -> Fraction:
    remaining = LOW_TAIL_MASS
    total = Fraction()
    for k in sorted(pmf):
        taken = min(remaining, pmf[k])
        total += k * taken
        remaining -= taken
        if remaining == 0:
            break
    if remaining:
        raise ValueError("insufficient mass")
    return total / LOW_TAIL_MASS


def dual_upper_polynomial(k: int) -> Fraction:
    """For integer k in [0,8], 1[k=0] <= (k-4)(k-5)/20."""
    if not 0 <= k <= N:
        raise ValueError("k must be in [0,8]")
    return Fraction((k - 4) * (k - 5), 20)


def solve_three_support(support: tuple[int, int, int]) -> dict[int, Fraction] | None:
    """Solve the exact three-moment system for one support vertex."""
    a, b, c = support
    rows = [
        [Fraction(1), Fraction(1), Fraction(1), Fraction(1)],
        [Fraction(a), Fraction(b), Fraction(c), TARGET_MEAN],
        [Fraction(a * (a - 1)), Fraction(b * (b - 1)),
         Fraction(c * (c - 1)), TARGET_FACTORIAL_SECOND],
    ]
    for col in range(3):
        pivot = next((r for r in range(col, 3) if rows[r][col]), None)
        if pivot is None:
            return None
        rows[col], rows[pivot] = rows[pivot], rows[col]
        scale = rows[col][col]
        rows[col] = [v / scale for v in rows[col]]
        for r in range(3):
            if r != col:
                factor = rows[r][col]
                rows[r] = [v - factor * w for v, w in zip(rows[r], rows[col])]
    weights = [row[3] for row in rows]
    if any(w < 0 for w in weights):
        return None
    return dict(zip(support, weights))


def vertex_extrema() -> tuple[Fraction, Fraction, int]:
    """Independent exhaustive vertex check: 3 equality constraints imply <=3 support."""
    feasible = []
    for support in combinations(range(N + 1), 3):
        law = solve_three_support(support)
        if law is not None:
            validate(law)
            feasible.append(law.get(0, Fraction()))
    if not feasible:
        raise AssertionError("no feasible vertices")
    return min(feasible), max(feasible), len(feasible)


def audit() -> dict:
    for law in (ZERO_TAIL, MAX_TAIL, INDEPENDENT):
        validate(law)
    # Exact dual certificate for EVERY feasible count law, not only vertices.
    assert all(
        dual_upper_polynomial(k) >= int(k == 0) for k in range(N + 1)
    )
    assert sum(
        (p * dual_upper_polynomial(k) for k, p in MAX_TAIL.items()), Fraction()
    ) == Fraction(1, 10)
    minimum, maximum, vertices = vertex_extrema()
    assert (minimum, maximum) == (Fraction(), Fraction(1, 10))
    assert ZERO_TAIL.get(0, Fraction()) == minimum
    assert MAX_TAIL[0] == maximum

    def report(pmf: dict[int, Fraction]) -> dict:
        return {
            "count_pmf_exact": {str(k): str(v) for k, v in sorted(pmf.items())},
            "zero_success_probability_exact": str(pmf.get(0, Fraction())),
            "zero_success_probability": float(pmf.get(0, Fraction())),
            "lower_10pct_mean_successes_exact": str(lower_decile(pmf)),
            "mean_successes_exact": str(moments(pmf)[1]),
            "pairwise_joint_success_exact": str(selected_success_probability(pmf, 2)),
        }

    return {
        "schema": "pcro/e260/pairwise-tail-nonidentifiability/v1",
        "candidate_count": N,
        "all_28_pairwise_correlations": "0 (exact under exchangeability)",
        "marginal_success_probability": "1/2",
        "exact_zero_tail_bounds": [str(minimum), str(maximum)],
        "feasible_three_support_vertices_checked": vertices,
        "independent_baseline": report(INDEPENDENT),
        "zero_tail_extreme": report(ZERO_TAIL),
        "max_tail_extreme": report(MAX_TAIL),
        "maximum_to_independent_zero_tail_ratio": "128/5",
        "dual_certificate": "1[K=0] <= (K-4)*(K-5)/20 for integer K in [0,8]",
        "claim": "Pairwise independence does not identify eight-way zero-success risk (PROVEN for abstract exchangeable Bernoulli model)",
        "limitations": [
            "These are mathematical distributions, not observed replay outcomes.",
            "No real evaluator, agent, policy or replay-family covariance was measured.",
            "Pairwise independence does not imply joint independence.",
            "No exploit, attack trace, hidden evaluation or third-party access occurred.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
