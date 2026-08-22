from pcro.replay_simulator import SimCandidate, simulate_replay


def test_simulator_is_reproducible():
    candidates = [
        SimCandidate("a", "f", "cell-a", 16, 0.8, 100, 10),
        SimCandidate("b", "g", "cell-b", 16, 0.8, 100, 10),
    ]
    one = simulate_replay(candidates, 500, trials=200, seed=7)
    two = simulate_replay(candidates, 500, trials=200, seed=7)
    assert one == two


def test_tight_budget_has_more_timeout_risk():
    candidates = [
        SimCandidate(str(index), "f", str(index), 16, 1.0, 100, 20)
        for index in range(5)
    ]
    tight = simulate_replay(candidates, 300, trials=500, seed=4)
    loose = simulate_replay(candidates, 1000, trials=500, seed=4)
    assert tight.timeout_rate > loose.timeout_rate
    assert tight.mean_completed < loose.mean_completed
