"""E184: independent Monte Carlo audit of family-correlation marginal calibration.

Run: python experiments/e184_family_marginal_audit.py
Synthetic distributions only. No evaluator access or hidden outcomes.
"""
from __future__ import annotations

import json
import math
import random
from statistics import mean


def old_probability_draw(probabilities: list[float], strength: float, rng: random.Random):
    p = min(0.999, max(0.001, mean(probabilities)))
    family = rng.betavariate(max(0.01, p * strength), max(0.01, (1 - p) * strength))
    return [max(0.0, min(1.0, 0.5 * (value + family))) for value in probabilities]


def corrected_outcomes(probabilities: list[float], strength: float, rng: random.Random):
    shared_weight = 0.5 / math.sqrt(1.0 + strength)
    shared_uniform = rng.random()
    outcomes = []
    for p in probabilities:
        if p <= 0:
            outcomes.append(False)
        elif p >= 1:
            outcomes.append(True)
        elif rng.random() < shared_weight:
            outcomes.append(shared_uniform < p)
        else:
            outcomes.append(rng.random() < p)
    return outcomes


def audit(probabilities: list[float], trials: int = 100_000, seed: int = 1729):
    strength = 20.0
    old_rng, new_rng = random.Random(seed), random.Random(seed)
    old_counts = [0] * len(probabilities)
    new_counts = [0] * len(probabilities)
    for _ in range(trials):
        old_probs = old_probability_draw(probabilities, strength, old_rng)
        for j, p in enumerate(old_probs):
            old_counts[j] += old_rng.random() < p
        new_outcomes = corrected_outcomes(probabilities, strength, new_rng)
        for j, outcome in enumerate(new_outcomes):
            new_counts[j] += outcome
    return {
        "probabilities": probabilities,
        "strength": strength,
        "trials": trials,
        "old_rates": [v / trials for v in old_counts],
        "new_rates": [v / trials for v in new_counts],
        "old_expected": [
            0.5 * (p + min(0.999, max(0.001, mean(probabilities))))
            for p in probabilities
        ],
    }


if __name__ == "__main__":
    print(json.dumps([audit(p) for p in ([0.0], [1.0], [0.1, 0.9], [0.25, 0.75])], indent=2))
