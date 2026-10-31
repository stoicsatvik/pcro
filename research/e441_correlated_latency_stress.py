"""E441: frozen synthetic common-mode latency stress on E426 fixed-prefix policies.

No real evaluator, security payload, external service, or policy promotion.
128 E426 holdout seeds x 64 draws; all candidate lists frozen before noise.
"""
from __future__ import annotations
import json
from pcro.runtime import ReplayScheduler
from research.e406_prefix_knapsack_gap import fixture
from research.e426_latency_uncertainty import (
    BUDGET, DRAWS, N, SEEDS, exact_ids, latency_noise, options,
)

MODES = ("independent", "half_shared", "fully_shared")
METHODS = ("greedy100", "exact100", "greedy85", "exact85")


def factors(seed: int, draw: int, count: int, mode: str) -> list[float]:
    """Equal marginal 0.7..1.3 uniform for endpoints; mixed case narrows marginal.

    Common factor uses a separately salted deterministic draw. This is an
    analyst-defined stress model, not measured replay latency.
    """
    if mode not in MODES or count < 1:
        raise ValueError("unfrozen latency mode or empty candidate list")
    independent = latency_noise(seed, draw, count)
    common = latency_noise(seed ^ 0xA5A5A5A5, draw ^ 0x5A5A5A5A, 1)[0]
    if mode == "independent":
        return independent
    if mode == "fully_shared":
        return [common] * count
    return [(x + common) / 2 for x in independent]


def realized(cases, ids: tuple[str, ...], multipliers: list[float]) -> tuple[int, bool]:
    if len(multipliers) != len(cases):
        raise ValueError("latency vector does not match candidate population")
    by_id = {case.name: (i, case) for i, case in enumerate(cases)}
    cost, reward = 0.0, 0
    for name in ids:
        i, case = by_id[name]
        if cost + case.cost_ms * multipliers[i] > BUDGET:
            return reward, True
        cost += case.cost_ms * multipliers[i]
        reward += case.reward
    return reward, False


def evaluate() -> dict:
    totals = {mode: {method: {"reward": 0, "truncated": 0} for method in METHODS}
              for mode in MODES}
    paired = {mode: [] for mode in MODES}
    for seed in SEEDS:
        cases = fixture(seed, n=N)
        opts = options(cases)
        schedules = {}
        for label, cap in (("100", BUDGET), ("85", 340)):
            schedules["greedy" + label] = ReplayScheduler().pack_for_budget(opts, cap).ordered_ids
            schedules["exact" + label] = exact_ids(cases, cap)
        per_seed = {mode: [] for mode in MODES}
        for draw in DRAWS:
            for mode in MODES:
                multipliers = factors(seed, draw, N, mode)
                observed = {}
                for method in METHODS:
                    reward, truncated = realized(cases, schedules[method], multipliers)
                    observed[method] = reward
                    totals[mode][method]["reward"] += reward
                    totals[mode][method]["truncated"] += int(truncated)
                per_seed[mode].append(observed["exact100"] - observed["greedy100"])
        for mode in MODES:
            paired[mode].append(sum(per_seed[mode]) / len(DRAWS))
    denom = len(SEEDS) * len(DRAWS)
    return {
        "experiment": "E441_SYNTHETIC_COMMON_MODE_LATENCY_STRESS",
        "seeds": len(SEEDS), "draws_per_seed": len(DRAWS),
        "candidate_count": N, "budget_ms": BUDGET,
        "modes": {
            mode: {
                "methods": {method: {
                    "mean_realized_reward": totals[mode][method]["reward"] / denom,
                    "truncation_fraction": totals[mode][method]["truncated"] / denom,
                } for method in METHODS},
                "paired_exact_minus_greedy": sum(paired[mode]) / len(SEEDS),
                "seed_wins_losses_ties": [
                    sum(x > 0 for x in paired[mode]),
                    sum(x < 0 for x in paired[mode]),
                    sum(x == 0 for x in paired[mode]),
                ],
            } for mode in MODES
        },
        "limitations": [
            "Only synthetic additive rewards and hypothetical latency correlation.",
            "Shared factor is a deterministic common shock, not measured network latency.",
            "Mixed 50/50 shock narrows marginal variance and is not a pure correlation intervention.",
            "E426 seeds are reused, so this is sensitivity analysis, not independent prospective replication.",
            "No authorized evaluator replay, security bypass, or deployment.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True, allow_nan=False))
