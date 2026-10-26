"""E287 exact k-wise catastrophic-tail identifiability frontier."""
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "e287_kwise_tail_identifiability_frontier",
    Path(__file__).resolve().parents[1] / "experiments"
    / "e287_kwise_tail_identifiability_frontier.py",
)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


@pytest.mark.parametrize("order,upper,vertices", [
    (1, Fraction(1, 2), 24),
    (2, Fraction(1, 10), 31),
    (3, Fraction(1, 16), 35),
    (4, Fraction(1, 40), 25),
    (5, Fraction(1, 72), 25),
    (6, Fraction(1, 112), 18),
    (7, Fraction(1, 128), 9),
    (8, Fraction(1, 256), 1),
])
def test_exact_frontier_and_attaining_laws(order, upper, vertices):
    result = M.extrema(order)
    assert result["upper"] == upper
    assert result["feasible_bases"] == vertices
    assert result["lower"] == (Fraction(1, 256) if order == 8 else 0)
    for key in ("upper_law", "lower_law"):
        assert M.moments(result[key], order) == tuple(
            M.moment_target(j) for j in range(order + 1)
        )
        M.verify_kwise(result[key], order)


def test_fourwise_bound_is_six_point_four_times_independence():
    r = M.extrema(4)
    assert r["upper"] / Fraction(1, 256) == Fraction(32, 5)
    assert r["lower"] == 0


def test_sevenwise_does_not_imply_eightwise():
    r = M.extrema(7)
    assert r["upper"] == Fraction(1, 128)
    assert r["lower"] == 0
    assert r["upper"] != Fraction(1, 256)


def test_eightwise_identifies_tail_exactly():
    r = M.extrema(8)
    assert r["lower"] == r["upper"] == Fraction(1, 256)


def test_bad_order_and_support_fail_closed():
    for order in (0, 9):
        with pytest.raises(ValueError):
            M.extrema(order)
    with pytest.raises(ValueError):
        M.solve_support((0, 0), 1)


def test_machine_receipt_deterministic_and_not_empirical():
    receipt = M.audit()
    assert receipt == M.audit()
    assert json.dumps(receipt, sort_keys=True) == json.dumps(M.audit(), sort_keys=True)
    assert len(receipt["independence_orders"]) == 8
    assert "No observed" in receipt["limitations"][1]
