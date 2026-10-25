"""Exact third-order independence and tail-bound regression tests for E276."""
import importlib.util
import json
import math
from fractions import Fraction
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "e276_triplewise_tail_nonidentifiability",
    Path(__file__).resolve().parents[1] / "experiments"
    / "e276_triplewise_tail_nonidentifiability.py",
)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


@pytest.mark.parametrize("law", [M.ZERO_TAIL, M.MAX_TAIL, M.INDEPENDENT])
def test_every_three_way_pattern_is_independent(law):
    M.validate(law)
    M.verify_every_triple(law)
    joint = M.full_joint(law)
    assert len(joint) == 256
    assert sum(joint.values(), Fraction()) == 1


def test_exact_four_moments_and_extreme_tails():
    for law in (M.ZERO_TAIL, M.MAX_TAIL, M.INDEPENDENT):
        assert M.factorial_moments(law) == (1, 4, 14, 42)
    assert M.ZERO_TAIL.get(0, Fraction()) == 0
    assert M.MAX_TAIL[0] == Fraction(1, 16)
    assert M.INDEPENDENT[0] == Fraction(1, 256)
    assert M.MAX_TAIL[0] / M.INDEPENDENT[0] == 16


def test_dual_certificate_exact_for_every_count_and_law():
    for k in range(9):
        assert M.dual_upper(k) >= int(k == 0)
    for law in (M.ZERO_TAIL, M.MAX_TAIL, M.INDEPENDENT):
        assert sum((p * M.dual_upper(k) for k, p in law.items()), Fraction()) == Fraction(1, 16)


def test_exhaustive_four_support_vertices():
    minimum, maximum, feasible = M.vertex_extrema()
    assert (minimum, maximum, feasible) == (0, Fraction(1, 16), 35)
    assert math.comb(9, 4) == 126


def test_invalid_laws_and_counts_fail():
    with pytest.raises(ValueError):
        M.validate({0: Fraction(1)})
    with pytest.raises(ValueError):
        M.validate({0: 0.1, 4: 0.9})
    with pytest.raises(ValueError):
        M.dual_upper(9)


def test_receipt_is_reproducible_and_not_empirical():
    first = M.audit()
    assert first == M.audit()
    assert json.dumps(first, sort_keys=True) == json.dumps(M.audit(), sort_keys=True)
    assert first["exact_all_fail_bounds"] == ["0", "1/16"]
    assert first["four_support_vertices_checked"] == 35
    assert "No observed" in first["limitations"][0]
