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


def test_exact_probability_boundaries_survive_mixed_family_shock():
    candidates = [
        SimCandidate("never", "same-family", "never-cell", 7, 0.0, 10),
        SimCandidate("always", "same-family", "always-cell", 3, 1.0, 10),
    ]
    for seed in (0, 1, 13):
        outcome = simulate_replay(candidates, 100, trials=1000, novelty_bonus=0, seed=seed)
        assert outcome.mean_raw_score == 3.0
        assert outcome.p10_raw_score == outcome.p50_raw_score == outcome.p90_raw_score == 3.0
        assert outcome.timeout_rate == 0.0
        assert outcome.mean_completed == 2.0


def test_exact_probability_boundaries_survive_homogeneous_family_shock():
    for probability, expected_score in ((0.0, 0.0), (1.0, 11.0)):
        candidates = [SimCandidate("boundary", "family", "cell", 11, probability, 10)]
        outcome = simulate_replay(candidates, 100, trials=1000, novelty_bonus=0, seed=17)
        assert outcome.mean_raw_score == expected_score
        assert outcome.p10_raw_score == expected_score
        assert outcome.p90_raw_score == expected_score


def test_interior_probability_seeded_regression_for_marginal_preserving_law():
    candidates = [
        SimCandidate("a", "same", "a", 16, 0.23, 100, 20),
        SimCandidate("b", "same", "b", 9, 0.67, 130, 35),
        SimCandidate("c", "other", "c", 4, 0.82, 80, 0),
    ]
    # E184 replaces the biased beta-family blend with a marginal-preserving
    # common-uniform mixture. Old goldens represented the rejected law.
    # These exact results were independently reproduced with a separate
    # synthetic reference implementation using Python's seeded RNG.
    expected = {
        0: (15.777, 0.025, 2.975),
        7: (16.659, 0.021, 2.978),
        83: (16.014, 0.017, 2.983),
    }
    for seed, (score, timeout_rate, completed) in expected.items():
        outcome = simulate_replay(candidates, 400, trials=1000, seed=seed)
        assert (outcome.mean_raw_score, outcome.timeout_rate, outcome.mean_completed) == (
            score,
            timeout_rate,
            completed,
        )
