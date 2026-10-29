from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class TraceEvent:
    """One event in a controlled synthetic tool-agent replay."""

    name: str
    ok: bool = True
    source: str = "trusted"
    side_effect: str | None = None
    scope: str = "normal"
    latency_ms: int = 100
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> TraceEvent:
        return cls(
            name=str(value["name"]),
            ok=bool(value.get("ok", True)),
            source=str(value.get("source", "trusted")),
            side_effect=value.get("side_effect"),
            scope=str(value.get("scope", "normal")),
            latency_ms=max(0, int(value.get("latency_ms", 100))),
            metadata=dict(value.get("metadata", {})),
        )


@dataclass(frozen=True)
class Trace:
    """A replayable synthetic trace used by the semantics laboratory."""

    trace_id: str
    events: tuple[TraceEvent, ...]
    messages: tuple[str, ...] = ()
    cell: str | None = None

    @property
    def replay_cost_ms(self) -> int:
        return sum(event.latency_ms for event in self.events)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Trace:
        return cls(
            trace_id=str(value["trace_id"]),
            events=tuple(TraceEvent.from_dict(event) for event in value.get("events", [])),
            messages=tuple(str(item) for item in value.get("messages", [])),
            cell=value.get("cell"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "events": [asdict(event) for event in self.events],
            "messages": list(self.messages),
            "cell": self.cell,
        }
