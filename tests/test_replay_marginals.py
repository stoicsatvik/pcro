"""Synthetic falsification gates for family-correlated replay marginals."""

import random

import pytest

from pcro.replay_simulator import SimCandidate, _correlated_success, simulate_replay


def test_certain_and_impossible_events_are_exact_at_all_family_shocks():
    rng = random.Random(17)
    for shared_uniform in (0.0, 0.01, 0.5, 0.99, 1.0):
        for _ in range(100):
            assert not _correlated_success(rng, 0.0, shared_uniform, 0.5)
            assert _correlated_success(rng, 1.0, shared_uniform, 0.5)


def test_heterogeneous_family_preserves_individual_marginals():
    rng = random.Random(23)
    n = 30_000
    counts = [0, 0]
    for _ in range(n):
        u = rng.random()
        for j, p in enumerate((0.1, 0.9)):
            counts[j] += _correlated_success(rng, p, u, 0.5)
    assert abs(counts[0] / n - 0.1) < 0.015
    assert abs(counts[1] / n - 0.9) < 0.015


def test_full_replay_does_not_inflate_rare_high_reward_candidate():
    candidates = [
        SimCandidate("rare", "shared", "rare-cell", 100, 0.1, 1),
        SimCandidate("common", "shared", "common-cell", 0, 0.9, 1),
    ]
    result = simulate_replay(candidates, 10, trials=30_000, novelty_bonus=0, seed=37)
    assert abs(result.mean_raw_score - 10.0) < 1.5
    assert result.mean_completed == 2


def test_family_shock_creates_positive_dependence_without_marginal_drift():
    rng = random.Random(31)
    n = 40_000
    both = 0
    for _ in range(n):
        u = rng.random()
        a = _correlated_success(rng, 0.5, u, 0.5)
        b = _correlated_success(rng, 0.5, u, 0.5)
        both += a and b
    # P(both) = .25 + (.5**2)*(.5-.25) = .3125
    assert abs(both / n - 0.3125) < 0.015


@pytest.mark.parametrize("strength", [-1.0, float("nan"), float("inf")])
def test_invalid_family_strength_fails_closed(strength):
    with pytest.raises(ValueError):
        simulate_replay([], 100, family_correlation_strength=strength)


def test_nonfinite_forecast_fails_closed():
    candidate = SimCandidate("bad", "f", "c", 1, float("nan"), 1)
    with pytest.raises(ValueError):
        simulate_replay([candidate], 100)
