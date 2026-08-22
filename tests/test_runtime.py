from pcro.runtime import ReplayOption, ReplayScheduler, RunningStats


def stats(*values):
    result = RunningStats()
    for value in values:
        result.observe(value)
    return result


def test_running_stats_tracks_variance():
    result = stats(100, 120, 80)
    assert result.n == 3
    assert result.mean_ms == 100
    assert result.std_ms > 0


def test_scheduler_prefers_robust_reward_density():
    fast = ReplayOption("fast", "a", 16, 0.9, stats(100, 105, 95))
    slow = ReplayOption("slow", "b", 20, 0.95, stats(500, 600, 400))
    ordered = ReplayScheduler().order([slow, fast])
    assert ordered[0].candidate_id == "fast"


def test_budget_returns_scored_prefix():
    first = ReplayOption("first", "a", 16, 1.0, stats(100))
    second = ReplayOption("second", "b", 16, 1.0, stats(100))
    prefix = ReplayScheduler().prefix_for_budget([first, second], 150)
    assert len(prefix.ordered_ids) == 1
    assert prefix.expected_reward == 16
