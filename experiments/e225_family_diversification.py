"""E225: exact synthetic replay-family diversification and lower-tail tradeoffs.

Abstract Bernoulli successes only. No third-party systems, attacks, hidden
competition tests, evaluator access, or empirical correlation estimates.
"""
from __future__ import annotations

import json
import math
import random


def family_pmf(n: int, p: float, strength: float) -> list[float]:
    if n < 1 or not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError("invalid family size or probability")
    if not math.isfinite(strength) or strength < 0:
        raise ValueError("invalid correlation strength")
    w = 0.5 / math.sqrt(1 + strength)
    high = w + (1 - w) * p
    low = (1 - w) * p
    return [
        math.comb(n, k)
        * (p * high**k * (1 - high) ** (n - k)
           + (1 - p) * low**k * (1 - low) ** (n - k))
        for k in range(n + 1)
    ]


def distribution(partition: tuple[int, ...], p: float, strength: float) -> list[float]:
    if not partition or any(n < 1 for n in partition):
        raise ValueError("nonempty positive family partition required")
    result = [1.0]
    for n in partition:
        family = family_pmf(n, p, strength)
        combined = [0.0] * (len(result) + len(family) - 1)
        for i, a in enumerate(result):
            for j, b in enumerate(family):
                combined[i + j] += a * b
        result = combined
    return result


def lower_tail_mean(pmf: list[float], alpha: float = 0.10) -> float:
    if not 0 < alpha <= 1 or not pmf or any(p < 0 for p in pmf):
        raise ValueError("invalid lower-tail distribution")
    if abs(sum(pmf) - 1) > 1e-9:
        raise ValueError("distribution must sum to one")
    mass = total = 0.0
    for k, p in enumerate(pmf):
        take = min(p, alpha - mass)
        total += k * take
        mass += take
        if mass >= alpha - 1e-14:
            break
    return total / alpha


def summary(pmf: list[float]) -> dict[str, float]:
    expected = sum(k * p for k, p in enumerate(pmf))
    return {
        "mean_successes": expected,
        "zero_success_probability": pmf[0],
        "variance": sum((k - expected) ** 2 * p for k, p in enumerate(pmf)),
        "lower_10pct_mean_successes": lower_tail_mean(pmf),
    }


def simulate(partition: tuple[int, ...], p: float, strength: float,
             trials: int, seed: int) -> list[float]:
    """Independent seeded Monte Carlo implementation, not sampling the exact PMF."""
    if trials < 1:
        raise ValueError("trials must be positive")
    rng = random.Random(seed)
    w = 0.5 / math.sqrt(1 + strength)
    counts = [0] * (sum(partition) + 1)
    for _ in range(trials):
        successes = 0
        for n in partition:
            shared = rng.random()
            for _ in range(n):
                u = shared if rng.random() < w else rng.random()
                successes += int(u < p)
        counts[successes] += 1
    return [count / trials for count in counts]


def audit(trials: int = 20_000, seed: int = 225024) -> dict:
    scenarios = []
    partitions = ((8,), (4, 4), (2, 2, 2, 2), (1,) * 8)
    for strength in (0.0, 20.0, 100.0):
        for index, partition in enumerate(partitions):
            exact = distribution(partition, 0.5, strength)
            sampled = simulate(partition, 0.5, strength, trials, seed + index + int(strength))
            scenarios.append({
                "family_sizes": list(partition),
                "strength": strength,
                "pair_correlation_within_family": 0.25 / (1 + strength),
                "exact": summary(exact),
                "max_histogram_error": max(abs(a - b) for a, b in zip(exact, sampled)),
            })
    higher_mean_cluster = summary(distribution((8,), 0.7, 0.0))
    lower_mean_diverse = summary(distribution((1,) * 8, 0.5, 0.0))
    assert higher_mean_cluster["mean_successes"] > lower_mean_diverse["mean_successes"]
    assert higher_mean_cluster["lower_10pct_mean_successes"] < (
        lower_mean_diverse["lower_10pct_mean_successes"]
    )
    assert all(s["max_histogram_error"] < 0.025 for s in scenarios)
    return {
        "schema": "pcro/e225/synthetic-family-diversification/v1",
        "trials_per_scenario": trials,
        "seed": seed,
        "scenarios": scenarios,
        "mean_vs_tail_counterexample": {
            "clustered_8_at_p_0_7": higher_mean_cluster,
            "diverse_8_at_p_0_5": lower_mean_diverse,
        },
        "claim": "SUPPORTED exact synthetic family model; real replay dependence NOT YET PROVEN",
        "caveat": "Correlation law is assumed, not calibrated; synthetic results are not evaluator performance.",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
