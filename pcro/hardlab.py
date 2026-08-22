"""High-signal benchmark diagnostics over abstract event skeletons."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass

from .guardrail_lab import score_ensemble
from .reachability import public_u2a_certificate
from .semantics_lab import enumerate_short_skeletons


@dataclass(frozen=True)
class HardLabRow:
    trace_id: str
    tools: tuple[str, ...]
    public_reward: int
    mean_reward: float
    worst_reward: int
    cvar_reward: float
    replay_cost_ms: int
    public_density_per_second: float
    robust_density_per_second: float


def run_hardlab(max_events: int = 3, top: int = 20) -> dict:
    traces = enumerate_short_skeletons(max_events=max_events)
    rows: list[HardLabRow] = []
    reward_distribution: Counter[int] = Counter()
    for trace in traces:
        score = score_ensemble(trace)
        reward_distribution[score.public_reward] += 1
        seconds = max(0.001, trace.replay_cost_ms / 1000.0)
        robust = 0.5 * score.cvar_reward + 0.5 * score.worst_reward
        rows.append(
            HardLabRow(
                trace_id=trace.trace_id,
                tools=tuple(event.name for event in trace.events),
                public_reward=score.public_reward,
                mean_reward=score.mean_reward,
                worst_reward=score.worst_reward,
                cvar_reward=score.cvar_reward,
                replay_cost_ms=trace.replay_cost_ms,
                public_density_per_second=score.public_reward / seconds,
                robust_density_per_second=robust / seconds,
            )
        )
    rows.sort(
        key=lambda row: (row.robust_density_per_second, row.public_density_per_second),
        reverse=True,
    )
    certificate = public_u2a_certificate()
    return {
        "n_traces": len(traces),
        "reward_distribution": dict(sorted(reward_distribution.items())),
        "u2a_reachability": asdict(certificate),
        "top": [asdict(row) for row in rows[:top]],
    }
