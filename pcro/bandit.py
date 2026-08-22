"""Lightweight Bayesian learner for selecting trace families under replay cost."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable


@dataclass
class Arm:
    name: str
    reward_if_success: float
    expected_cost_ms: float
    alpha: float = 1.0
    beta: float = 1.0

    @property
    def posterior_mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def expected_value(self) -> float:
        return self.posterior_mean * self.reward_if_success

    @property
    def expected_density(self) -> float:
        return self.expected_value / max(1.0, self.expected_cost_ms)

    def observe(self, success: bool, cost_ms: float | None = None) -> None:
        if success:
            self.alpha += 1.0
        else:
            self.beta += 1.0
        if cost_ms is not None and cost_ms >= 0:
            self.expected_cost_ms = 0.8 * self.expected_cost_ms + 0.2 * cost_ms

    def thompson_density(self, rng: random.Random) -> float:
        sampled_success = rng.betavariate(self.alpha, self.beta)
        return sampled_success * self.reward_if_success / max(1.0, self.expected_cost_ms)

    def lower_confidence_success(self, z: float = 1.2815515655446004) -> float:
        a, b = self.alpha, self.beta
        mean = a / (a + b)
        variance = a * b / ((a + b) ** 2 * (a + b + 1.0))
        return max(0.0, mean - z * math.sqrt(variance))

    def robust_density(self) -> float:
        return self.lower_confidence_success() * self.reward_if_success / max(
            1.0, self.expected_cost_ms
        )


class ThompsonScheduler:
    def __init__(self, arms: Iterable[Arm], seed: int = 0) -> None:
        self.arms = list(arms)
        if not self.arms:
            raise ValueError("at least one arm is required")
        self.rng = random.Random(seed)

    def choose(self) -> Arm:
        return max(self.arms, key=lambda arm: arm.thompson_density(self.rng))

    def robust_ranking(self) -> list[Arm]:
        return sorted(self.arms, key=lambda arm: arm.robust_density(), reverse=True)
