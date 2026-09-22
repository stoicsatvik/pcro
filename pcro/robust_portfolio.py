"""Robust candidate portfolio construction under replay budget and novelty economics."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class CandidateForecast:
    candidate_id: str
    family: str
    cell_hash: str
    reward_by_policy: Mapping[str, float]
    success_by_policy: Mapping[str, float]
    conservative_latency_ms: float
    semantic_validity: float = 0.0

    def expected_policy_rewards(self, novelty: float = 0.0) -> tuple[float, ...]:
        policies = sorted(set(self.reward_by_policy) | set(self.success_by_policy))
        rewards: list[float] = []
        for policy in policies:
            success = min(1.0, max(0.0, float(self.success_by_policy.get(policy, 0.0))))
            reward = max(0.0, float(self.reward_by_policy.get(policy, 0.0)))
            rewards.append(success * (reward + novelty))
        return tuple(rewards)


@dataclass(frozen=True)
class PortfolioSelection:
    selected_ids: tuple[str, ...]
    cells: tuple[str, ...]
    conservative_cost_ms: float
    robust_expected_reward: float
    mean_expected_reward: float
    family_counts: Mapping[str, int]


def lower_tail_mean(values: Iterable[float], alpha: float = 0.5) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    count = max(1, int(len(ordered) * min(1.0, max(0.0, alpha))))
    return mean(ordered[:count])


def _marginal_value(
    candidate: CandidateForecast,
    *,
    seen_cells: set[str],
    family_count: int,
    novelty_bonus: float,
    cvar_alpha: float,
    family_penalty: float,
    semantic_weight: float,
) -> tuple[float, float]:
    novelty = novelty_bonus if candidate.cell_hash not in seen_cells else 0.0
    expected = candidate.expected_policy_rewards(novelty)
    robust = lower_tail_mean(expected, cvar_alpha)
    average = mean(expected) if expected else 0.0
    concentration_cost = family_penalty * family_count * max(1.0, robust)
    semantic_bonus = semantic_weight * min(1.0, max(0.0, candidate.semantic_validity))
    return max(0.0, robust - concentration_cost + semantic_bonus), average


def select_robust_portfolio(
    candidates: Iterable[CandidateForecast],
    budget_ms: float,
    *,
    max_findings: int = 2_000,
    novelty_bonus: float = 2.0,
    cvar_alpha: float = 0.5,
    family_penalty: float = 0.08,
    semantic_weight: float = 0.25,
) -> PortfolioSelection:
    remaining = list(candidates)
    budget = max(0.0, float(budget_ms))
    seen_cells: set[str] = set()
    selected: list[CandidateForecast] = []
    family_counts: dict[str, int] = {}
    robust_total = 0.0
    mean_total = 0.0
    cost_total = 0.0

    while remaining and len(selected) < max_findings:
        best_index: int | None = None
        best_density = -1.0
        best_robust = 0.0
        best_mean = 0.0
        for index, candidate in enumerate(remaining):
            cost = max(1.0, candidate.conservative_latency_ms)
            if cost > budget:
                continue
            robust, average = _marginal_value(
                candidate,
                seen_cells=seen_cells,
                family_count=family_counts.get(candidate.family, 0),
                novelty_bonus=novelty_bonus,
                cvar_alpha=cvar_alpha,
                family_penalty=family_penalty,
                semantic_weight=semantic_weight,
            )
            density = robust / cost
            if density > best_density:
                best_index = index
                best_density = density
                best_robust = robust
                best_mean = average
        if best_index is None or best_density <= 0:
            break

        candidate = remaining.pop(best_index)
        cost = max(1.0, candidate.conservative_latency_ms)
        selected.append(candidate)
        budget -= cost
        cost_total += cost
        robust_total += best_robust
        mean_total += best_mean
        seen_cells.add(candidate.cell_hash)
        family_counts[candidate.family] = family_counts.get(candidate.family, 0) + 1

    return PortfolioSelection(
        selected_ids=tuple(candidate.candidate_id for candidate in selected),
        cells=tuple(sorted(seen_cells)),
        conservative_cost_ms=cost_total,
        robust_expected_reward=robust_total,
        mean_expected_reward=mean_total,
        family_counts=dict(family_counts),
    )
