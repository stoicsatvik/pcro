from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .model import Trace


@dataclass(frozen=True)
class PredicateHit:
    name: str
    severity: int
    event_index: int | None = None
    detail: str = ""


@dataclass(frozen=True)
class PredicateSpec:
    name: str
    severity: int
    evaluate: Callable[[Trace], list[PredicateHit]]


def _side_effect(trace: Trace) -> list[PredicateHit]:
    hits: list[PredicateHit] = []
    for index, event in enumerate(trace.events):
        if event.ok and event.side_effect:
            hits.append(PredicateHit("SYNTH_SIDE_EFFECT", 3, index, event.side_effect))
    return hits


def _source_to_effect(trace: Trace) -> list[PredicateHit]:
    """Toy temporal rule for controlled experiments only.

    A hit occurs when a successful synthetic side effect is preceded within two
    events by a synthetic untrusted-source marker.
    """

    hits: list[PredicateHit] = []
    for index, event in enumerate(trace.events):
        if not (event.ok and event.side_effect):
            continue
        start = max(0, index - 2)
        if any(previous.source == "untrusted" for previous in trace.events[start:index]):
            hits.append(PredicateHit("SYNTH_SOURCE_TO_EFFECT", 5, index, event.side_effect))
    return hits


def _protected_scope(trace: Trace) -> list[PredicateHit]:
    hits: list[PredicateHit] = []
    for index, event in enumerate(trace.events):
        if event.ok and event.side_effect == "WRITE" and event.scope == "protected":
            hits.append(PredicateHit("SYNTH_PROTECTED_WRITE", 4, index, event.name))
    return hits


def _repeated_effect(trace: Trace) -> list[PredicateHit]:
    indices = [
        index
        for index, event in enumerate(trace.events)
        if event.ok and event.side_effect is not None
    ]
    if len(indices) < 2:
        return []
    return [PredicateHit("SYNTH_REPEATED_EFFECT", 2, indices[-1], f"count={len(indices)}")]


DEFAULT_PREDICATES: tuple[PredicateSpec, ...] = (
    PredicateSpec("SYNTH_SIDE_EFFECT", 3, _side_effect),
    PredicateSpec("SYNTH_SOURCE_TO_EFFECT", 5, _source_to_effect),
    PredicateSpec("SYNTH_PROTECTED_WRITE", 4, _protected_scope),
    PredicateSpec("SYNTH_REPEATED_EFFECT", 2, _repeated_effect),
)


def evaluate_predicates(
    trace: Trace, predicates: tuple[PredicateSpec, ...] = DEFAULT_PREDICATES
) -> list[PredicateHit]:
    hits: list[PredicateHit] = []
    for predicate in predicates:
        hits.extend(predicate.evaluate(trace))
    return hits
