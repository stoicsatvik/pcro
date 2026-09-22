from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExperimentRecord:
    trace_id: str
    desired_signature: str
    actual_signature: str
    predicate_vector: dict[str, int]
    replay_cost_ms: int
    success: bool
    failure_stage: str | None = None
    notes: str = ""
    family: str = "unknown"
    model: str = "unknown"
    guardrail: str = "unknown"
    evaluator_version: str = "unknown"
    predicate_reward: float = 0.0
    cell_hash: str | None = None
    features: tuple[float, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class JsonlExperimentStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: ExperimentRecord) -> None:
        payload: dict[str, Any] = asdict(record)
        payload["recorded_at"] = datetime.now(UTC).isoformat()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def summarize(self) -> dict[str, Any]:
        rows = self.read_all()
        successes = sum(bool(row.get("success")) for row in rows)
        total_cost = sum(int(row.get("replay_cost_ms", 0)) for row in rows)
        total_reward = sum(float(row.get("predicate_reward", 0.0)) for row in rows)
        return {
            "experiments": len(rows),
            "successes": successes,
            "success_rate": successes / len(rows) if rows else 0.0,
            "total_replay_cost_ms": total_cost,
            "total_predicate_reward": total_reward,
            "reward_per_second": total_reward / max(0.001, total_cost / 1000.0),
        }
