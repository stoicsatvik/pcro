"""Parity checks between PCRO's evaluator mirror and the installed public SDK.

When ``aicomp_sdk`` is available, randomized traces are passed through both implementations. This
turns source reverse-engineering into a continuously testable contract and catches silent drift.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .jed_contract import eval_jed_predicates, score_cell_hash
from .model import Trace, TraceEvent
from .properties import random_trace


@dataclass(frozen=True)
class ParityMismatch:
    trace_id: str
    kind: str
    pcro: Any
    official: Any


@dataclass(frozen=True)
class ParityReport:
    sdk_available: bool
    traces_checked: int
    predicate_mismatches: int
    cell_mismatches: int
    mismatches: tuple[ParityMismatch, ...]

    @property
    def passed(self) -> bool:
        return self.sdk_available and not self.mismatches

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["passed"] = self.passed
        return payload


def _event_mapping(event: TraceEvent) -> dict[str, Any]:
    metadata = event.metadata
    args = metadata.get("args", {})
    error = metadata.get("error", "")
    return {
        "name": event.name,
        "args": args if isinstance(args, dict) else {},
        "ok": bool(event.ok),
        "output": metadata.get("output", ""),
        "side_effect": event.side_effect,
        "scope": event.scope,
        "source": event.source,
        # The pinned public SDK treats this field as a string and calls string methods on it.
        # Synthetic traces without an error therefore lower to the contract's empty-string value,
        # never JSON/Python null.
        "error": "" if error is None else str(error),
    }


def trace_mapping(trace: Trace) -> dict[str, Any]:
    return {
        "tool_events": [_event_mapping(event) for event in trace.events],
        "user_messages": list(trace.messages),
    }


def _hit_key(predicate: Any) -> tuple[str, int]:
    if isinstance(predicate, dict):
        return str(predicate.get("predicate")), int(predicate.get("severity", 1))
    return str(predicate.predicate), int(predicate.severity)


def compare_trace(trace: Trace) -> tuple[ParityMismatch, ...]:
    try:
        from aicomp_sdk.core.cells import cell_signature as official_cell_signature
        from aicomp_sdk.core.predicates import eval_predicates as official_eval_predicates
    except ImportError as exc:
        raise RuntimeError("aicomp_sdk is not installed") from exc

    mapping = trace_mapping(trace)
    official_hits = tuple(sorted(_hit_key(hit) for hit in official_eval_predicates(mapping)))
    pcro_hits = tuple(sorted(_hit_key(hit) for hit in eval_jed_predicates(trace)))
    official_cell = official_cell_signature(mapping["tool_events"])["hash"]
    pcro_cell = score_cell_hash(trace)
    mismatches: list[ParityMismatch] = []
    if official_hits != pcro_hits:
        mismatches.append(ParityMismatch(trace.trace_id, "predicates", pcro_hits, official_hits))
    if official_cell != pcro_cell:
        mismatches.append(ParityMismatch(trace.trace_id, "score_cell", pcro_cell, official_cell))
    return tuple(mismatches)


def run_parity(traces: Iterable[Trace]) -> ParityReport:
    try:
        import aicomp_sdk  # noqa: F401
    except ImportError:
        return ParityReport(False, 0, 0, 0, ())

    materialized = list(traces)
    mismatches: list[ParityMismatch] = []
    for trace in materialized:
        mismatches.extend(compare_trace(trace))
    return ParityReport(
        sdk_available=True,
        traces_checked=len(materialized),
        predicate_mismatches=sum(mismatch.kind == "predicates" for mismatch in mismatches),
        cell_mismatches=sum(mismatch.kind == "score_cell" for mismatch in mismatches),
        mismatches=tuple(mismatches),
    )


def run_random_parity(seeds: int = 200) -> ParityReport:
    return run_parity(random_trace(seed) for seed in range(seeds))
