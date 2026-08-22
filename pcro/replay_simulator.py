"""Monte Carlo replay-risk simulation for a fixed candidate order."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class SimCandidate:
    candidate_id: str
    family: str
    cell_hash: str
    predicate_reward: float
    success_probability: float
    latency_mean_ms: float
    latency_std_ms: float = 0.0


@dataclass(frozen=True)
class ReplayDistribution:
    trials: int
    mean_raw_score: float
    p10_raw_score: float
    p50_raw_score: float
    p90_raw_score: float
    timeout_rate: float
    mean_completed: float


def _quantile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    index = min(len(sorted_values) - 1, max(0, round(q * (len(sorted_values) - 1))))
    return float(sorted_values[index])


def _sample_positive_latency(rng: random.Random, mean_ms: float, std_ms: float) -> float:
    mean_ms = max(1.0, mean_ms)
    std_ms = max(0.0, std_ms)
    if std_ms == 0:
        return mean_ms
    variance = std_ms * std_ms
    sigma2 = math.log1p(variance / (mean_ms * mean_ms))
    sigma = math.sqrt(max(0.0, sigma2))
    mu = math.log(mean_ms) - 0.5 * sigma2
    return rng.lognormvariate(mu, sigma)


def _family_reliability(
    rng: random.Random,
    candidates: Sequence[SimCandidate],
    strength: float,
) -> Mapping[str, float]:
    by_family: dict[str, list[float]] = {}
    for candidate in candidates:
        by_family.setdefault(candidate.family, []).append(candidate.success_probability)
    result: dict[str, float] = {}
    for family, probabilities in by_family.items():
        p = min(0.999, max(0.001, mean(probabilities)))
        alpha = max(0.01, p * strength)
        beta = max(0.01, (1.0 - p) * strength)
        result[family] = rng.betavariate(alpha, beta)
    return result


def simulate_replay(
    ordered_candidates: Iterable[SimCandidate],
    budget_ms: float,
    *,
    trials: int = 2_000,
    novelty_bonus: float = 2.0,
    family_correlation_strength: float = 20.0,
    seed: int = 0,
) -> ReplayDistribution:
    candidates = list(ordered_candidates)
    if trials <= 0:
        raise ValueError("trials must be positive")
    rng = random.Random(seed)
    scores: list[float] = []
    completed_counts: list[int] = []
    timeouts = 0

    for _ in range(trials):
        family_draw = _family_reliability(rng, candidates, family_correlation_strength)
        elapsed = 0.0
        raw = 0.0
        completed = 0
        cells: set[str] = set()
        timed_out = False
        for candidate in candidates:
            latency = _sample_positive_latency(
                rng, candidate.latency_mean_ms, candidate.latency_std_ms
            )
            if elapsed + latency > budget_ms:
                timed_out = True
                break
            elapsed += latency
            completed += 1
            base_p = min(1.0, max(0.0, candidate.success_probability))
            family_p = family_draw[candidate.family]
            # Blend individual forecast with a shared family shock. This induces common-mode
            # failures without pretending we know the true hidden correlation structure.
            p = min(1.0, max(0.0, 0.5 * base_p + 0.5 * family_p))
            if rng.random() < p:
                raw += max(0.0, candidate.predicate_reward)
                if candidate.cell_hash not in cells:
                    raw += novelty_bonus
                    cells.add(candidate.cell_hash)
        scores.append(raw)
        completed_counts.append(completed)
        timeouts += int(timed_out)

    ordered_scores = sorted(scores)
    return ReplayDistribution(
        trials=trials,
        mean_raw_score=mean(scores),
        p10_raw_score=_quantile(ordered_scores, 0.10),
        p50_raw_score=_quantile(ordered_scores, 0.50),
        p90_raw_score=_quantile(ordered_scores, 0.90),
        timeout_rate=timeouts / trials,
        mean_completed=mean(completed_counts),
    )
