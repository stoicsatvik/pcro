"""Dependency-free online surrogate ranker.

A small linear model is deliberately used before neural networks: benchmark data is initially
sparse, and this model makes feature/reward bugs easy to audit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp
from typing import Iterable, Sequence


def sigmoid(value: float) -> float:
    if value >= 0:
        z = exp(-value)
        return 1.0 / (1.0 + z)
    z = exp(value)
    return z / (1.0 + z)


@dataclass
class OnlineLogisticRanker:
    n_features: int
    learning_rate: float = 0.05
    l2: float = 1e-4
    weights: list[float] = field(init=False)
    bias: float = 0.0

    def __post_init__(self) -> None:
        if self.n_features <= 0:
            raise ValueError("n_features must be positive")
        self.weights = [0.0] * self.n_features

    def predict_proba(self, features: Sequence[float]) -> float:
        if len(features) != self.n_features:
            raise ValueError("feature dimension mismatch")
        logit = self.bias + sum(weight * value for weight, value in zip(self.weights, features))
        return sigmoid(logit)

    def update(self, features: Sequence[float], label: int) -> float:
        if label not in {0, 1}:
            raise ValueError("label must be 0 or 1")
        prediction = self.predict_proba(features)
        error = float(label) - prediction
        for index, value in enumerate(features):
            self.weights[index] += self.learning_rate * (
                error * value - self.l2 * self.weights[index]
            )
        self.bias += self.learning_rate * error
        return prediction

    def fit(self, rows: Iterable[tuple[Sequence[float], int]], epochs: int = 10) -> None:
        materialized = list(rows)
        for _ in range(epochs):
            for features, label in materialized:
                self.update(features, label)
