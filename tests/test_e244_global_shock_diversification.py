"""E244 exact global-shock mixture and independent simulation controls."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "e244_global_shock_diversification",
    Path(__file__).resolve().parents[1] / "experiments" / "e244_global_shock_diversification.py",
)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


@pytest.mark.parametrize("partition", M.PARTITIONS)
@pytest.mark.parametrize("q", M.GLOBAL_WEIGHTS)
def test_marginals_and_distribution(partition, q):
    d = M.global_shock_pmf(partition, 0.5, 0.0, q)
    assert sum(d) == pytest.approx(1.0)
    assert M.summary(d)["mean_successes"] == pytest.approx(4.0)
    assert d[0] >= q*0.5 - 1e-12


def test_q_zero_equals_existing_e225_law():
    from experiments.e225_family_diversification import distribution
    for partition in M.PARTITIONS:
        assert M.global_shock_pmf(partition, 0.5, 0.0, 0.0) == pytest.approx(
            distribution(partition, 0.5, 0.0)
        )


def test_q_one_erases_family_diversification():
    for partition in M.PARTITIONS:
        d = M.global_shock_pmf(partition, 0.5, 0.0, 1.0)
        assert d[0] == pytest.approx(0.5)
        assert d[-1] == pytest.approx(0.5)
        assert sum(d[1:-1]) == pytest.approx(0.0)


def test_diverse_with_common_shock_worse_than_clustered_without():
    clustered = M.summary(M.global_shock_pmf((8,),0.5,0.0,0.0))
    diverse = M.summary(M.global_shock_pmf((1,)*8,0.5,0.0,0.1))
    assert diverse["zero_success_probability"] > clustered["zero_success_probability"]
    assert diverse["lower_10pct_mean_successes"] > 0


def test_independent_simulation_matches_exact():
    part = (2,2,2,2)
    exact = M.global_shock_pmf(part,0.5,0.0,0.25)
    sampled = M.simulate_global_shock(part,0.5,0.0,0.25,20_000,244)
    assert max(abs(a-b) for a,b in zip(exact,sampled)) < 0.025
    assert sampled == M.simulate_global_shock(part,0.5,0.0,0.25,20_000,244)


@pytest.mark.parametrize("q",[-0.01,1.01,float("nan"),float("inf")])
def test_invalid_global_weight_rejected(q):
    with pytest.raises(ValueError):
        M.global_shock_pmf((8,),0.5,0.0,q)


def test_invalid_trials_rejected():
    with pytest.raises(ValueError):
        M.simulate_global_shock((8,),0.5,0.0,0.1,0,244)
