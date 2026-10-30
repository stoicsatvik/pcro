"""E406 synthetic, non-operational replay packing falsification tests."""

from research.e406_prefix_knapsack_gap import Case, density_pack, evaluate, exact_oracle, fixture


def test_lcg_fixture_is_pinned():
    cases = fixture(0)
    assert [(case.reward, case.cost_ms) for case in cases[:3]] == [
        (17, 70), (67, 56), (69, 26)
    ]


def test_constructed_counterexample_exposes_density_gap():
    cases = [
        Case("high-density", 60, 60),
        Case("pair-a", 49, 50),
        Case("pair-b", 49, 51),
    ]
    greedy, ids = density_pack(cases, 101)
    optimum, oracle_ids = exact_oracle(cases, 101)
    assert (greedy, ids) == (60, ("high-density",))
    assert (optimum, oracle_ids) == (98, ("pair-a", "pair-b"))


def test_exact_oracle_agrees_with_independent_integer_dp():
    cases = fixture(37)
    for budget in (100, 160, 220):
        dp = [0] * (budget + 1)
        for case in cases:
            for capacity in range(budget, case.cost_ms - 1, -1):
                dp[capacity] = max(dp[capacity], dp[capacity - case.cost_ms] + case.reward)
        assert exact_oracle(cases, budget)[0] == dp[budget]


def test_frozen_384_case_receipt_and_negative_result():
    result = evaluate()
    assert result["cases"] == 384
    assert result["suboptimal"] == 94
    assert result["suboptimal_fraction"] == 94 / 384
    assert result["mean_regret"] == 3.5078125
    assert result["max_regret"] == 60
    assert result["per_budget"]["100"]["suboptimal"] == 28
    assert result["per_budget"]["160"]["suboptimal"] == 27
    assert result["per_budget"]["220"]["suboptimal"] == 39
    assert result["worst_case"]["seed"] == 37
    assert result["worst_case"]["budget_ms"] == 100
    assert result["worst_case"]["density_reward"] == 22
    assert result["worst_case"]["oracle_reward"] == 82


def test_oracle_rejects_negative_budget():
    try:
        exact_oracle(fixture(0), -1)
    except ValueError:
        pass
    else:
        raise AssertionError("negative budget must fail")
