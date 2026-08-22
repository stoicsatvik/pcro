from pcro.runtime import ReplayOption, ReplayScheduler, RunningStats


def stats(value):
    result = RunningStats()
    result.observe(value)
    return result


def test_fixed_prefix_does_not_skip_candidate_that_times_out():
    big = ReplayOption("big", "big", 100, 1.0, stats(200))
    small = ReplayOption("small", "small", 10, 1.0, stats(40))
    scheduler = ReplayScheduler()

    fixed = scheduler.simulate_prefix([big, small], 150)
    assert fixed.ordered_ids == ()
    assert fixed.next_candidate_id == "big"


def test_pre_replay_packer_can_omit_oversized_candidate_before_list_is_fixed():
    big = ReplayOption("big", "big", 100, 1.0, stats(200))
    small = ReplayOption("small", "small", 10, 1.0, stats(40))
    scheduler = ReplayScheduler()

    packed = scheduler.pack_for_budget([big, small], 150)
    assert packed.ordered_ids == ("small",)
    assert packed.expected_reward == 10
