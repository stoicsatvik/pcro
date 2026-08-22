"""Pareto ranking for score, robustness, semantics, and replay cost."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ObjectivePoint:
    candidate_id: str
    public_reward: float
    robust_reward: float
    semantic_validity: float
    replay_cost_ms: float

    def vector(self) -> tuple[float, float, float, float]:
        # First three are maximized; cost is minimized by negating it.
        return (
            self.public_reward,
            self.robust_reward,
            self.semantic_validity,
            -max(0.0, self.replay_cost_ms),
        )


def dominates(left: ObjectivePoint, right: ObjectivePoint) -> bool:
    a = left.vector()
    b = right.vector()
    return all(x >= y for x, y in zip(a, b)) and any(x > y for x, y in zip(a, b))


def pareto_front(points: Iterable[ObjectivePoint]) -> list[ObjectivePoint]:
    materialized = list(points)
    return [
        point
        for point in materialized
        if not any(other is not point and dominates(other, point) for other in materialized)
    ]


def pareto_layers(points: Iterable[ObjectivePoint]) -> list[list[ObjectivePoint]]:
    remaining = list(points)
    layers: list[list[ObjectivePoint]] = []
    while remaining:
        front = pareto_front(remaining)
        layers.append(front)
        front_ids = {id(point) for point in front}
        remaining = [point for point in remaining if id(point) not in front_ids]
    return layers
