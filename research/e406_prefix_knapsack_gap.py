"""E406: exact knapsack oracle against the existing pre-replay density packer.

All cases are synthetic abstract costs/rewards, not security attack traces.
The evaluator's fixed-prefix rule is not changed: optimization occurs BEFORE
the candidate list is submitted.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from pcro.runtime import ReplayOption, ReplayScheduler, RunningStats


@dataclass(frozen=True)
class Case:
    name: str
    reward: int
    cost_ms: int


def fixture(seed: int, n: int = 6) -> list[Case]:
    """Version-independent 32-bit LCG with no hidden tuning or random search."""
    state = (seed + 1) & 0xFFFFFFFF
    result = []
    for index in range(n):
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        reward = 5 + state % 96
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        cost = 10 + state % 111
        result.append(Case(f"s{seed}-c{index}", reward, cost))
    return result


def exact_oracle(cases: list[Case], budget_ms: int) -> tuple[int, tuple[str, ...]]:
    """Enumerate every subset; exact only for these six-candidate fixtures."""
    if budget_ms < 0:
        raise ValueError("negative budget")
    best_reward = 0
    best_names: tuple[str, ...] = ()
    for mask in range(1 << len(cases)):
        selected = [case for index, case in enumerate(cases) if mask & (1 << index)]
        if sum(case.cost_ms for case in selected) > budget_ms:
            continue
        reward = sum(case.reward for case in selected)
        names = tuple(sorted(case.name for case in selected))
        if reward > best_reward or (reward == best_reward and names < best_names):
            best_reward, best_names = reward, names
    return best_reward, best_names


def density_pack(cases: list[Case], budget_ms: int) -> tuple[int, tuple[str, ...]]:
    """Call the actual PCRO scheduler, not an independent reimplementation."""
    options = []
    for case in cases:
        latency = RunningStats()
        latency.observe(case.cost_ms)
        options.append(ReplayOption(case.name, "synthetic", case.reward, 1.0, latency))
    packed = ReplayScheduler().pack_for_budget(options, budget_ms)
    assert packed.conservative_cost_ms <= budget_ms
    return int(packed.expected_reward), packed.ordered_ids


def evaluate() -> dict:
    budgets = (100, 160, 220)
    outcomes = []
    for seed in range(128):
        cases = fixture(seed)
        for budget in budgets:
            optimal, oracle_ids = exact_oracle(cases, budget)
            greedy, density_ids = density_pack(cases, budget)
            if not 0 <= greedy <= optimal:
                raise AssertionError("oracle or packer violated reward bounds")
            outcomes.append({
                "seed": seed,
                "budget_ms": budget,
                "oracle_reward": optimal,
                "density_reward": greedy,
                "regret": optimal - greedy,
                "oracle_ids": oracle_ids,
                "density_ids": density_ids,
            })
    worst = sorted(
        outcomes, key=lambda row: (-row["regret"], row["seed"], row["budget_ms"])
    )[0]
    per_budget = {
        str(budget): {
            "cases": 128,
            "suboptimal": sum(
                row["regret"] > 0 for row in outcomes if row["budget_ms"] == budget
            ),
            "mean_regret": sum(
                row["regret"] for row in outcomes if row["budget_ms"] == budget
            ) / 128,
        }
        for budget in budgets
    }
    suboptimal = sum(row["regret"] > 0 for row in outcomes)
    return {
        "experiment": "E406_PCREPLAY_DENSITY_ORACLE",
        "cases": len(outcomes),
        "suboptimal": suboptimal,
        "suboptimal_fraction": suboptimal / len(outcomes),
        "mean_regret": sum(row["regret"] for row in outcomes) / len(outcomes),
        "max_regret": worst["regret"],
        "worst_case": worst,
        "per_budget": per_budget,
        "scope": (
            "Six synthetic independent candidates; deterministic latency and reward; "
            "no novelty overlap, guardrail uncertainty, real replays or attack execution."
        ),
        "claim_state": "DENSITY GLOBAL OPTIMALITY REJECTED FOR TESTED SYNTHETIC CASES",
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True, allow_nan=False))
