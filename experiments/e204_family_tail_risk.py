"""E204: exact family-dependence tail-risk falsification, synthetic only.

No evaluator, competition submission, hidden test, or third-party target is used.
Run: python experiments/e204_family_tail_risk.py
"""
from __future__ import annotations

import json
import math
import random


def exact_distribution(n: int, p: float, strength: float) -> list[float]:
    """Independent closed form for n equal-p members of one family.

    Conditional on the family's shared uniform U, successes are independent
    Bernoulli(q_high) if U < p, otherwise Bernoulli(q_low).
    """
    if n < 1 or not 0 <= p <= 1 or not math.isfinite(strength) or strength < 0:
        raise ValueError("invalid n, probability, or concentration")
    w = 0.5 / math.sqrt(1 + strength)
    q_high = w + (1 - w) * p
    q_low = (1 - w) * p
    return [
        math.comb(n, k) * (
            p * q_high**k * (1 - q_high)**(n - k)
            + (1 - p) * q_low**k * (1 - q_low)**(n - k)
        )
        for k in range(n + 1)
    ]


def independent_distribution(n: int, p: float) -> list[float]:
    return [math.comb(n, k) * p**k * (1 - p)**(n-k) for k in range(n+1)]


def moments(distribution: list[float]) -> dict[str, float]:
    mu = sum(k * v for k, v in enumerate(distribution))
    variance = sum((k - mu)**2 * v for k, v in enumerate(distribution))
    return {"mean": mu, "variance": variance, "zero_success_probability": distribution[0],
            "all_success_probability": distribution[-1]}


def sample_distribution(n: int, p: float, strength: float, trials: int, seed: int) -> list[float]:
    """Separate seeded simulation, not an invocation of the closed-form formula."""
    if trials < 1:
        raise ValueError("trials must be positive")
    rng = random.Random(seed)
    w = 0.5 / math.sqrt(1 + strength)
    histogram = [0] * (n + 1)
    for _ in range(trials):
        shared = rng.random()
        successes = 0
        for _ in range(n):
            u = shared if rng.random() < w else rng.random()
            successes += u < p
        histogram[successes] += 1
    return [v / trials for v in histogram]


def audit(n: int = 8, p: float = 0.5, trials: int = 40_000, seed: int = 204024) -> dict:
    independent = independent_distribution(n, p)
    baseline = moments(independent)
    scenarios = []
    for strength in (0.0, 20.0, 100.0):
        exact = exact_distribution(n, p, strength)
        observed = sample_distribution(n, p, strength, trials, seed)
        expected = moments(exact)
        sampled = moments(observed)
        w = 0.5 / math.sqrt(1 + strength)
        predicted_variance = n * p * (1-p) * (1 + (n-1)*w*w)
        assert abs(sum(exact) - 1) < 1e-12
        assert abs(expected["mean"] - n*p) < 1e-12
        assert abs(expected["variance"] - predicted_variance) < 1e-12
        scenarios.append({
            "strength": strength,
            "pair_correlation": w*w,
            "exact": expected,
            "sampled": sampled,
            "max_bin_absolute_error": max(abs(a-b) for a,b in zip(exact, observed)),
            "zero_success_risk_multiplier_vs_independent": (
                expected["zero_success_probability"] / baseline["zero_success_probability"]
            ),
        })
    return {
        "schema": "pcro/e204/synthetic-family-tail-risk/v1",
        "population": {"same_family_candidates": n, "marginal_success_probability": p,
                       "trials_per_strength": trials, "seed": seed},
        "independent_null": baseline,
        "scenarios": scenarios,
        "claim_state": "SUPPORTED exact synthetic law; real replay dependence NOT YET PROVEN",
        "limitation": "No empirical replay data; correlation parameter is not calibrated.",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
