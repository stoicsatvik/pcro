from pcro.bandit import Arm, ThompsonScheduler
from pcro.rl import QLearner, Transition
from pcro.surrogate import OnlineLogisticRanker


def test_bandit_learns_successful_low_cost_arm():
    fast = Arm("fast", reward_if_success=16, expected_cost_ms=100)
    slow = Arm("slow", reward_if_success=20, expected_cost_ms=500)
    for _ in range(20):
        fast.observe(True, 100)
        slow.observe(False, 500)
    scheduler = ThompsonScheduler([slow, fast], seed=7)
    assert scheduler.robust_ranking()[0].name == "fast"


def test_q_learning_learns_rewarding_action():
    learner = QLearner(actions=("good", "bad"), epsilon=0.2, seed=3)

    def step(state, action):
        return Transition(next_state=state, reward=1.0 if action == "good" else -1.0, done=True)

    learner.train("s", step, episodes=200, max_steps=1)
    assert learner.policy(["s"])["s"] == "good"


def test_online_surrogate_separates_simple_examples():
    model = OnlineLogisticRanker(2, learning_rate=0.2)
    rows = [
        ([1.0, 1.0], 1),
        ([1.0, 0.5], 1),
        ([-1.0, -1.0], 0),
        ([-1.0, -0.5], 0),
    ]
    model.fit(rows, epochs=40)
    assert model.predict_proba([1.0, 1.0]) > model.predict_proba([-1.0, -1.0])
