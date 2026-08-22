from __future__ import annotations

from dataclasses import dataclass

from .model import Trace
from .scoring import Score, score_trace


@dataclass(frozen=True)
class Portfolio:
    selected: tuple[Score, ...]
    total_value: int
    total_cost_ms: int


def rank_traces(traces: list[Trace]) -> list[Score]:
    scored = [score_trace(trace) for trace in traces]
    return sorted(
        scored,
        key=lambda item: (item.density_per_second, item.total_value),
        reverse=True,
    )


def select_under_budget(traces: list[Trace], budget_ms: int) -> Portfolio:
    """Greedy density baseline for the replay-budget optimisation problem."""

    if budget_ms < 0:
        raise ValueError("budget_ms must be non-negative")

    selected: list[Score] = []
    total_cost = 0
    seen_cells: set[str] = set()

    by_id = {trace.trace_id: trace for trace in traces}
    for preliminary in rank_traces(traces):
        trace = by_id[preliminary.trace_id]
        rescored = score_trace(trace, seen_cells=seen_cells)
        if total_cost + rescored.replay_cost_ms > budget_ms:
            continue
        if rescored.total_value <= 0:
            continue

        selected.append(rescored)
        total_cost += rescored.replay_cost_ms
        if trace.cell is not None:
            seen_cells.add(trace.cell)

    return Portfolio(
        selected=tuple(selected),
        total_value=sum(item.total_value for item in selected),
        total_cost_ms=total_cost,
    )
