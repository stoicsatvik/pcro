"""E426 synthetic fixed-prefix latency falsification; no external evaluator calls."""
from research.e406_prefix_knapsack_gap import exact_oracle, fixture
from research.e426_latency_uncertainty import (
    evaluate,
    exact_ids,
    latency_noise,
    options,
    realized,
)
from pcro.runtime import ReplayScheduler


def test_exact_dp_agrees_with_exhaustive_subset_oracle():
    for seed in (128, 129, 130):
        cases = fixture(seed, n=12)
        by_id = {case.name: case for case in cases}
        for budget in (200, 400, 600):
            names = exact_ids(cases, budget)
            assert sum(by_id[name].reward for name in names) == exact_oracle(
                cases, budget
            )[0]
            assert sum(by_id[name].cost_ms for name in names) <= budget


def test_realized_fixed_prefix_and_reproducible_noise():
    cases = fixture(128, n=24)
    assert latency_noise(128, 0, 24) == latency_noise(128, 0, 24)
    assert latency_noise(128, 0, 24) != latency_noise(128, 1, 24)
    selected = ReplayScheduler().pack_for_budget(options(cases), 400).ordered_ids
    reward, truncated = realized(cases, selected, 128, 0)
    assert 0 <= reward <= sum(case.reward for case in cases)
    assert isinstance(truncated, bool)


def test_frozen_latency_holdout_receipt():
    result = evaluate()
    assert result["seeds"] == 128
    assert result["draws_per_seed"] == 64
    assert result["candidate_count"] == 24
    g = result["results"]["greedy100"]
    d = result["results"]["exact100"]
    assert g["nominal_mean"] == 657.515625
    assert d["nominal_mean"] == 664.578125
    assert g["realized_mean"] == 642.4522705078125
    assert d["realized_mean"] == 639.470703125
    assert g["truncation_fraction"] == 0.3087158203125
    assert d["truncation_fraction"] == 0.4033203125
    assert result["paired_exact_minus_greedy_realized"] == -2.9815673828125
    assert (
        result["paired_seed_wins"],
        result["paired_seed_losses"],
        result["paired_seed_ties"],
    ) == (17, 48, 63)


def test_negative_budget_fails_closed():
    try:
        exact_ids(fixture(128, n=12), -1)
    except ValueError:
        pass
    else:
        raise AssertionError("negative budget must be rejected")
