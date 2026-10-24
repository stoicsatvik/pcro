"""Independent exact probability controls for the E204 synthetic audit."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "e204_family_tail_risk", Path(__file__).resolve().parents[1] / "experiments" / "e204_family_tail_risk.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_equal_marginals_but_more_joint_extremes():
    independent = MODULE.independent_distribution(8, 0.5)
    correlated = MODULE.exact_distribution(8, 0.5, 0)
    assert sum(correlated) == pytest.approx(1)
    assert MODULE.moments(independent)["mean"] == pytest.approx(4)
    assert MODULE.moments(correlated)["mean"] == pytest.approx(4)
    assert correlated[0] > independent[0] * 10
    assert correlated[8] > independent[8] * 10
    assert MODULE.moments(correlated)["variance"] == pytest.approx(5.5)


def test_dependence_weakens_as_concentration_increases():
    independent = MODULE.independent_distribution(8, 0.5)
    risks = [MODULE.exact_distribution(8, 0.5, x)[0] for x in (0, 20, 100)]
    assert risks[0] > risks[1] > risks[2] > independent[0]


def test_independent_monte_carlo_matches_closed_form():
    expected = MODULE.exact_distribution(8, 0.5, 20)
    measured = MODULE.sample_distribution(8, 0.5, 20, 30_000, 123)
    assert max(abs(a-b) for a, b in zip(expected, measured)) < 0.012


@pytest.mark.parametrize("args", [(0, 0.5, 20), (8, -0.1, 20), (8, 1.1, 20), (8, 0.5, -1), (8, 0.5, float("nan"))])
def test_invalid_inputs_fail_closed(args):
    with pytest.raises(ValueError):
        MODULE.exact_distribution(*args)
