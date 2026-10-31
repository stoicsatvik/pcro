"""E441 fixed-seed, non-operational latency correlation sensitivity checks."""
from research.e426_latency_uncertainty import latency_noise
from research.e441_correlated_latency_stress import MODES, evaluate, factors, realized
from research.e406_prefix_knapsack_gap import fixture


def test_frozen_noise_endpoints_and_reproducibility():
    for mode in MODES:
        a = factors(128, 0, 24, mode)
        assert a == factors(128, 0, 24, mode)
        assert len(a) == 24 and all(0.7 <= x < 1.3 for x in a)
    assert factors(128, 0, 24, "independent") == latency_noise(128, 0, 24)
    assert len(set(factors(128, 0, 24, "fully_shared"))) == 1


def test_invalid_mode_and_vector_fail_closed():
    try:
        factors(128, 0, 24, "unregistered")
    except ValueError:
        pass
    else:
        raise AssertionError("mode must be frozen")
    try:
        realized(fixture(128, n=24), (), [1.0])
    except ValueError:
        pass
    else:
        raise AssertionError("vector length must match")


def test_e426_independent_receipt_unchanged():
    result = evaluate()
    independent = result["modes"]["independent"]
    assert independent["methods"]["greedy100"]["mean_realized_reward"] == 642.4522705078125
    assert independent["methods"]["exact100"]["mean_realized_reward"] == 639.470703125
    assert independent["paired_exact_minus_greedy"] == -2.9815673828125
    assert independent["seed_wins_losses_ties"] == [17, 48, 63]


def test_all_modes_have_complete_finite_metrics():
    result = evaluate()
    assert set(result["modes"]) == set(MODES)
    for group in result["modes"].values():
        assert sum(group["seed_wins_losses_ties"]) == 128
        for method in group["methods"].values():
            assert 0 <= method["mean_realized_reward"] <= 2400
            assert 0 <= method["truncation_fraction"] <= 1
