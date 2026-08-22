from pcro.multiobjective import ObjectivePoint, dominates, pareto_front, pareto_layers


def test_pareto_front_keeps_public_vs_robust_tradeoff():
    public_only = ObjectivePoint("public", 20, 0, 0.1, 100)
    robust = ObjectivePoint("robust", 16, 16, 0.8, 130)
    dominated = ObjectivePoint("dominated", 10, 0, 0.0, 200)
    front = pareto_front([public_only, robust, dominated])
    assert {point.candidate_id for point in front} == {"public", "robust"}
    assert dominates(public_only, dominated)
    assert len(pareto_layers([public_only, robust, dominated])) == 2
