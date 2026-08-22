from __future__ import annotations

from dataclasses import dataclass

from .model import Trace
from .predicates import PredicateHit, evaluate_predicates


SEVERITY_WEIGHTS = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}


@dataclass(frozen=True)
class Score:
    trace_id: str
    hits: tuple[PredicateHit, ...]
    predicate_reward: int
    diversity_bonus: int
    total_value: int
    replay_cost_ms: int
    density_per_second: float


def score_trace(trace: Trace, *, seen_cells: set[str] | None = None) -> Score:
    hits = tuple(evaluate_predicates(trace))
    predicate_reward = sum(SEVERITY_WEIGHTS[hit.severity] for hit in hits)

    diversity_bonus = 0
    if trace.cell is not None and (seen_cells is None or trace.cell not in seen_cells):
        diversity_bonus = 2

    total_value = predicate_reward + diversity_bonus
    replay_cost_ms = max(trace.replay_cost_ms, 1)
    density_per_second = total_value / (replay_cost_ms / 1000)

    return Score(
        trace_id=trace.trace_id,
        hits=hits,
        predicate_reward=predicate_reward,
        diversity_bonus=diversity_bonus,
        total_value=total_value,
        replay_cost_ms=replay_cost_ms,
        density_per_second=density_per_second,
    )
