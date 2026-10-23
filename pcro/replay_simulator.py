"""Monte Carlo replay-risk simulation for a fixed candidate order."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from statistics import mean
from collections.abc import Iterable, Sequence


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


def _correlated_success(
    rng: random.Random, probability: float, shared_uniform: float, shared_weight: float
) -> bool:
    """A common-uniform mixture preserves each Bernoulli marginal exactly.

    Each event uses the family's common uniform with probability shared_weight,
    otherwise an independent uniform. For equal-probability family members,
    their Bernoulli correlation is shared_weight**2. Unlike blending the
    probability with a family-average beta draw, this does not bias rare and
    high-confidence members toward their family's mean.
    """
    if probability <= 0.0:
        return False
    if probability >= 1.0:
        return True
    if rng.random() < shared_weight:
        return shared_uniform < probability
    return rng.random() < probability


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
    if not math.isfinite(family_correlation_strength) or family_correlation_strength < 0:
        raise ValueError("family_correlation_strength must be finite and nonnegative")
    if any(not math.isfinite(c.success_probability) for c in candidates):
        raise ValueError("success probabilities must be finite")

    # Match the old beta-shock's approximate equal-pair correlation, 1/[4*(s+1)],
    # without sacrificing individual forecast marginals. This is a modelling
    # choice, not a measured correlation estimate.
    shared_weight = 0.5 / math.sqrt(1.0 + family_correlation_strength)
    rng = random.Random(seed)
    scores: list[float] = []
    completed_counts: list[int] = []
    timeouts = 0

    for _ in range(trials):
        family_uniforms = {
            family: rng.random() for family in dict.fromkeys(c.family for c in candidates)
        }
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
            if _correlated_success(rng, base_p, family_uniforms[candidate.family], shared_weight):
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
