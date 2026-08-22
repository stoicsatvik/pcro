from pcro.robust_portfolio import CandidateForecast, select_robust_portfolio


def candidate(candidate_id, family, cell, reward, success, cost=100):
    return CandidateForecast(
        candidate_id=candidate_id,
        family=family,
        cell_hash=cell,
        reward_by_policy={"public": reward, "stress": reward},
        success_by_policy={"public": success, "stress": success},
        conservative_latency_ms=cost,
    )


def test_portfolio_values_new_cell_marginally():
    same_a = candidate("a", "f", "cell-a", 10, 1.0)
    same_b = candidate("b", "f", "cell-a", 10, 1.0)
    new = candidate("c", "f", "cell-c", 10, 1.0)
    selected = select_robust_portfolio(
        [same_a, same_b, new],
        200,
        family_penalty=0,
        semantic_weight=0,
    )
    assert "c" in selected.selected_ids
    assert len(selected.cells) == 2


def test_family_penalty_can_diversify_near_ties():
    a1 = candidate("a1", "family-a", "a1", 20, 1.0)
    a2 = candidate("a2", "family-a", "a2", 20, 1.0)
    b1 = candidate("b1", "family-b", "b1", 19.5, 1.0)
    selected = select_robust_portfolio(
        [a1, a2, b1],
        200,
        family_penalty=0.2,
        semantic_weight=0,
    )
    assert set(selected.selected_ids) == {"a1", "b1"}
