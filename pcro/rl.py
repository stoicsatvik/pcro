"""Tabular RL over abstract tool-event skeletons.

The learner operates on synthetic event labels only. It is useful for checking whether learned
planning adds value before introducing a large neural model.
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Callable, Hashable, Iterable
from dataclasses import dataclass

State = Hashable
Action = Hashable


@dataclass(frozen=True)
class Transition:
    next_state: State
    reward: float
    done: bool = False


class QLearner:
    def __init__(
        self,
        actions: Iterable[Action],
        alpha: float = 0.2,
        gamma: float = 0.95,
        epsilon: float = 0.1,
        seed: int = 0,
    ) -> None:
        self.actions = tuple(actions)
        if not self.actions:
            raise ValueError("actions cannot be empty")
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.rng = random.Random(seed)
        self.q: dict[tuple[State, Action], float] = defaultdict(float)

    def choose(self, state: State) -> Action:
        if self.rng.random() < self.epsilon:
            return self.rng.choice(self.actions)
        return max(self.actions, key=lambda action: self.q[(state, action)])

    def update(self, state: State, action: Action, transition: Transition) -> None:
        current = self.q[(state, action)]
        future = 0.0 if transition.done else max(
            self.q[(transition.next_state, candidate)] for candidate in self.actions
        )
        target = transition.reward + self.gamma * future
        self.q[(state, action)] = current + self.alpha * (target - current)

    def train(
        self,
        start_state: State,
        step: Callable[[State, Action], Transition],
        episodes: int = 100,
        max_steps: int = 8,
    ) -> None:
        for _ in range(episodes):
            state = start_state
            for _ in range(max_steps):
                action = self.choose(state)
                transition = step(state, action)
                self.update(state, action, transition)
                state = transition.next_state
                if transition.done:
                    break

    def policy(self, states: Iterable[State]) -> dict[State, Action]:
        return {
            state: max(self.actions, key=lambda action: self.q[(state, action)])
            for state in states
        }
