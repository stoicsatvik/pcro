"""Replay-latency uncertainty and partial-timeout-aware candidate ordering."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class RunningStats:
    n: int = 0
    mean_ms: float = 0.0
    m2: float = 0.0

    def observe(self, value_ms: float) -> None:
        value = max(0.0, float(value_ms))
        self.n += 1
        delta = value - self.mean_ms
        self.mean_ms += delta / self.n
        self.m2 += delta * (value - self.mean_ms)

    @property
    def variance(self) -> float:
        return self.m2 / (self.n - 1) if self.n > 1 else 0.0

    @property
    def std_ms(self) -> float:
        return math.sqrt(self.variance)

    def conservative_ms(self, z: float = 1.2815515655446004, fallback_ms: float = 1000.0) -> float:
        if self.n == 0:
            return fallback_ms
        return max(1.0, self.mean_ms + z * self.std_ms)


@dataclass
class ReplayOption:
    candidate_id: str
    family: str
    reward_if_success: float
    success_probability: float
    latency: RunningStats = field(default_factory=RunningStats)

    @property
    def expected_reward(self) -> float:
        return max(0.0, min(1.0, self.success_probability)) * max(0.0, self.reward_if_success)

    def robust_density(self, z: float = 1.2815515655446004) -> float:
        return self.expected_reward / self.latency.conservative_ms(z=z)


@dataclass(frozen=True)
class ScheduledPrefix:
    ordered_ids: tuple[str, ...]
    conservative_cost_ms: float
    expected_reward: float
    next_candidate_id: str | None = None


class ReplayScheduler:
    """Order findings so a replay timeout preserves the strongest expected prefix.

    The evaluator processes candidates sequentially. ``prefix_for_budget`` therefore stops at the
    first candidate that no longer fits the conservative remaining budget; it never skips that
    candidate and pretends later findings could still run.
    """

    def __init__(self, max_findings: int = 2_000) -> None:
        if max_findings <= 0:
            raise ValueError("max_findings must be positive")
        self.max_findings = max_findings

    def order(self, options: Iterable[ReplayOption], z: float = 1.2815515655446004) -> list[ReplayOption]:
        return sorted(options, key=lambda option: option.robust_density(z), reverse=True)[
            : self.max_findings
        ]

    def prefix_for_budget(
        self,
        options: Iterable[ReplayOption],
        budget_ms: float,
        *,
        z: float = 1.2815515655446004,
    ) -> ScheduledPrefix:
        remaining = max(0.0, float(budget_ms))
        selected: list[str] = []
        cost = 0.0
        reward = 0.0
        next_candidate_id: str | None = None
        for option in self.order(options, z=z):
            robust_cost = option.latency.conservative_ms(z=z)
            if robust_cost > remaining:
                next_candidate_id = option.candidate_id
                break
            selected.append(option.candidate_id)
            remaining -= robust_cost
            cost += robust_cost
            reward += option.expected_reward
        return ScheduledPrefix(tuple(selected), cost, reward, next_candidate_id)
