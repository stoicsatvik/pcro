from __future__ import annotations

import random

from .model import Trace, TraceEvent

TOOLS = ("observe", "inspect", "transform", "record", "publish")
EFFECTS = (None, None, None, "WRITE", "SHARE")


def generate_traces(count: int, *, seed: int = 7) -> list[Trace]:
    """Generate deterministic toy traces; no external systems are touched."""

    rng = random.Random(seed)
    traces: list[Trace] = []

    for trace_index in range(count):
        event_count = rng.randint(2, 7)
        events: list[TraceEvent] = []
        for _ in range(event_count):
            effect = rng.choice(EFFECTS)
            source = "untrusted" if rng.random() < 0.25 else "trusted"
            scope = "protected" if effect == "WRITE" and rng.random() < 0.25 else "normal"
            events.append(
                TraceEvent(
                    name=rng.choice(TOOLS),
                    ok=rng.random() > 0.08,
                    source=source,
                    side_effect=effect,
                    scope=scope,
                    latency_ms=rng.randint(40, 350),
                )
            )

        traces.append(
            Trace(
                trace_id=f"synthetic-{trace_index:04d}",
                events=tuple(events),
                messages=("synthetic benchmark task",),
                cell=f"cell-{rng.randint(0, max(2, count // 3))}",
            )
        )

    return traces
