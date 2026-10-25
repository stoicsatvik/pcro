"""E260 exact exchangeable Bernoulli tail and pairwise-moment controls."""
import importlib.util
import json
import math
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "e260_pairwise_tail_nonidentifiability",
    Path(__file__).resolve().parents[1] / "experiments"
    / "e260_pairwise_tail_nonidentifiability.py",
)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


@pytest.mark.parametrize("law", [M.ZERO_TAIL, M.MAX_TAIL, M.INDEPENDENT])
def test_every_individual_and_pair_is_exactly_independent(law):
    M.validate(law)
    # Independently construct the complete 2^8 joint law from uniform
    # selection of a subset conditional on K, not using the moment shortcut.
    outcomes = {
        mask: law.get(mask.bit_count(), Fraction())
        / math.comb(8, mask.bit_count())
        for mask in range(1 << 8)
    }
    assert sum(outcomes.values()) == 1
    for i in range(8):
        assert sum(p for mask, p in outcomes.items() if mask & (1 << i)) == Fraction(1, 2)
    for i, j in combinations(range(8), 2):
        assert sum(
            p for mask, p in outcomes.items()
            if mask & (1 << i) and mask & (1 << j)
        ) == Fraction(1, 4)


def test_exact_tail_bounds_and_constructive_attainment():
    minimum, maximum, count = M.vertex_extrema()
    assert count == 31
    assert minimum == 0
    assert maximum == Fraction(1, 10)
    assert M.ZERO_TAIL.get(0, Fraction()) == minimum
    assert M.MAX_TAIL[0] == maximum
    assert M.INDEPENDENT[0] == Fraction(1, 256)
    assert maximum / M.INDEPENDENT[0] == Fraction(128, 5)


def test_exact_dual_certificate_over_all_integer_counts():
    for k in range(9):
        assert M.dual_upper_polynomial(k) >= int(k == 0)
    # This expected value depends only on frozen first and second moments.
    for law in (M.ZERO_TAIL, M.MAX_TAIL, M.INDEPENDENT):
        bound = sum(
            (p * M.dual_upper_polynomial(k) for k, p in law.items()), Fraction()
        )
        assert bound == Fraction(1, 10)


def test_lower_tail_not_identified_either():
    assert M.lower_decile(M.MAX_TAIL) == 0
    assert M.lower_decile(M.ZERO_TAIL) == 2
    assert M.lower_decile(M.INDEPENDENT) == Fraction(103, 64)


def test_invalid_laws_rejected():
    with pytest.raises(ValueError):
        M.validate({0: Fraction(1)})
    with pytest.raises(ValueError):
        M.validate({0: Fraction(-1, 10), 4: Fraction(11, 10)})
    with pytest.raises(ValueError):
        M.validate({0: 0.1, 4: 0.9})
    with pytest.raises(ValueError):
        M.dual_upper_polynomial(9)


def test_machine_receipt_is_deterministic_and_conservative():
    first = M.audit()
    assert json.dumps(first, sort_keys=True) == json.dumps(M.audit(), sort_keys=True)
    assert first["exact_zero_tail_bounds"] == ["0", "1/10"]
    assert first["feasible_three_support_vertices_checked"] == 31
    assert "not observed replay" in " ".join(first["limitations"]).lower()
