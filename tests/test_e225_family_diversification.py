"""Exact and independently sampled controls for E225 family diversification."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "e225_family_diversification",
    Path(__file__).resolve().parents[1] / "experiments" / "e225_family_diversification.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_partition_invariance_of_expected_success_and_normalization():
    for strength in (0.0, 20.0, 100.0):
        for partition in ((8,), (4, 4), (2, 2, 2, 2), (1,) * 8):
            pmf = MODULE.distribution(partition, 0.5, strength)
            assert sum(pmf) == pytest.approx(1.0)
            assert MODULE.summary(pmf)["mean_successes"] == pytest.approx(4.0)


def test_diversification_improves_assumed_lower_tail():
    clustered = MODULE.summary(MODULE.distribution((8,), 0.5, 0))
    diverse = MODULE.summary(MODULE.distribution((1,) * 8, 0.5, 0))
    assert clustered["zero_success_probability"] > diverse["zero_success_probability"] * 10
    assert clustered["lower_10pct_mean_successes"] < diverse["lower_10pct_mean_successes"]
    assert clustered["mean_successes"] == pytest.approx(diverse["mean_successes"])


def test_higher_mean_can_still_have_worse_lower_tail():
    clustered = MODULE.summary(MODULE.distribution((8,), 0.7, 0))
    diverse = MODULE.summary(MODULE.distribution((1,) * 8, 0.5, 0))
    assert clustered["mean_successes"] > diverse["mean_successes"]
    assert clustered["lower_10pct_mean_successes"] < diverse["lower_10pct_mean_successes"]


def test_independent_monte_carlo_and_repeatability():
    exact = MODULE.distribution((4, 4), 0.5, 0)
    sample = MODULE.simulate((4, 4), 0.5, 0, 20_000, 123)
    assert sample == MODULE.simulate((4, 4), 0.5, 0, 20_000, 123)
    assert max(abs(a - b) for a, b in zip(exact, sample)) < 0.025


@pytest.mark.parametrize("partition,p,strength", [
    ((), 0.5, 0), ((0, 8), 0.5, 0), ((8,), -0.1, 0),
    ((8,), 1.1, 0), ((8,), 0.5, -1), ((8,), 0.5, float("nan")),
])
def test_invalid_parameters_fail_closed(partition, p, strength):
    with pytest.raises(ValueError):
        MODULE.distribution(partition, p, strength)


def test_invalid_lower_tail():
    with pytest.raises(ValueError):
        MODULE.lower_tail_mean([0.5, 0.5], alpha=0)
    with pytest.raises(ValueError):
        MODULE.lower_tail_mean([0.1, 0.1], alpha=0.1)
