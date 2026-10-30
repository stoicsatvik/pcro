"""E426: exact nominal packing versus realized fixed-prefix reward under latency uncertainty.

Synthetic abstract candidates only; no security attacks or actual evaluator replay.
Frozen E406 LCG seeds 128..255, 24 options, budget 400 ms, 64 draws/seed.
"""
from __future__ import annotations
import json
from research.e406_prefix_knapsack_gap import Case, fixture
from pcro.runtime import ReplayOption, ReplayScheduler, RunningStats

SEEDS = range(128, 256)
DRAWS = range(64)
BUDGET = 400
N = 24


def options(cases: list[Case]) -> list[ReplayOption]:
    result = []
    for case in cases:
        stats = RunningStats()
        stats.observe(case.cost_ms)
        result.append(ReplayOption(case.name, "synthetic", case.reward, 1.0, stats))
    return result


def exact_ids(cases: list[Case], budget: int) -> tuple[str, ...]:
    """Exact 0/1 integer-ms additive DP; not an oracle for correlated or continuous costs."""
    if budget < 0:
        raise ValueError("negative budget")
    dp: list[tuple[int, int, tuple[int, ...]]] = [(0, 0, ()) for _ in range(budget + 1)]
    for i, case in enumerate(cases):
        old = dp
        updated = old.copy()
        for b in range(case.cost_ms, budget + 1):
            value, cost, indices = old[b - case.cost_ms]
            candidate = (value + case.reward, cost + case.cost_ms, indices + (i,))
            current = updated[b]
            if candidate[0] > current[0] or (
                candidate[0] == current[0] and candidate[1] < current[1]
            ):
                updated[b] = candidate
        dp = updated
    selected_names = {cases[i].name for i in dp[budget][2]}
    return tuple(
        option.candidate_id for option in ReplayScheduler().order(options(cases))
        if option.candidate_id in selected_names
    )


def latency_noise(seed: int, draw: int, count: int) -> list[float]:
    state = (0x9E3779B9 ^ (seed * 2654435761) ^ (draw * 1013904223)) & 0xFFFFFFFF
    values = []
    for _ in range(count):
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        values.append(0.7 + 0.6 * state / 4294967296)
    return values


def realized(cases: list[Case], ids: tuple[str, ...], seed: int, draw: int) -> tuple[int, bool]:
    by_id = {case.name: (i, case) for i, case in enumerate(cases)}
    noise = latency_noise(seed, draw, len(cases))
    cost = 0.0
    reward = 0
    for name in ids:
        i, case = by_id[name]
        actual_cost = case.cost_ms * noise[i]
        if cost + actual_cost > BUDGET:
            return reward, True
        cost += actual_cost
        reward += case.reward
    return reward, False


def evaluate() -> dict:
    totals = {
        key: {"nominal": 0, "realized": 0, "truncated": 0}
        for key in ("greedy100", "exact100", "greedy85", "exact85")
    }
    seed_diffs = []
    for seed in SEEDS:
        cases = fixture(seed, n=N)
        replay_options = options(cases)
        ids = {}
        for suffix, budget in (("100", BUDGET), ("85", 340)):
            ids["greedy" + suffix] = ReplayScheduler().pack_for_budget(
                replay_options, budget
            ).ordered_ids
            ids["exact" + suffix] = exact_ids(cases, budget)
        by_id = {case.name: case for case in cases}
        for key, names in ids.items():
            totals[key]["nominal"] += sum(by_id[name].reward for name in names)
        differences = []
        for draw in DRAWS:
            outcomes = {}
            for key, names in ids.items():
                reward, truncated = realized(cases, names, seed, draw)
                outcomes[key] = reward
                totals[key]["realized"] += reward
                totals[key]["truncated"] += int(truncated)
            differences.append(outcomes["exact100"] - outcomes["greedy100"])
        seed_diffs.append(sum(differences) / len(differences))
    return {
        "experiment": "E426_SYNTHETIC_LATENCY_HOLDOUT",
        "seeds": len(SEEDS),
        "draws_per_seed": len(DRAWS),
        "candidate_count": N,
        "budget_ms": BUDGET,
        "results": {
            key: {
                "nominal_mean": value["nominal"] / len(SEEDS),
                "realized_mean": value["realized"] / (len(SEEDS) * len(DRAWS)),
                "truncation_fraction": value["truncated"] / (len(SEEDS) * len(DRAWS)),
            }
            for key, value in totals.items()
        },
        "paired_exact_minus_greedy_realized": sum(seed_diffs) / len(seed_diffs),
        "paired_seed_wins": sum(x > 0 for x in seed_diffs),
        "paired_seed_losses": sum(x < 0 for x in seed_diffs),
        "paired_seed_ties": sum(x == 0 for x in seed_diffs),
        "claim_state": "NOMINAL EXACT OPTIMALITY DOES NOT GUARANTEE REALIZED FIXED-PREFIX DOMINANCE",
        "scope": "Synthetic additive rewards, deterministic LCG costs, bounded independent latency noise; no real replay.",
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), sort_keys=True, indent=2, allow_nan=False))
