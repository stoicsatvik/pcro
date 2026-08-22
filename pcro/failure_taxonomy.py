"""Failure-stage taxonomy for replay learning.

Binary success labels throw away the information PCRO needs for efficient iteration. This module
classifies *where* a desired abstract trace diverged from the replayed trace.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .jed_contract import JEDPredicateHit
from .model import Trace, TraceEvent


class FailureStage(StrEnum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    PARSER_INVALID = "parser_invalid"
    NO_TOOL = "no_tool"
    WRONG_TOOL = "wrong_tool"
    WRONG_ARGS = "wrong_args"
    GUARDRAIL_DENIED = "guardrail_denied"
    TOOL_ERROR = "tool_error"
    PARTIAL_CHAIN = "partial_chain"
    PREDICATE_MISS = "predicate_miss"


@dataclass(frozen=True)
class FailureDiagnosis:
    stage: FailureStage
    matched_prefix: int
    desired_steps: int
    actual_steps: int
    progress: float
    reason: str


def _args(event: TraceEvent) -> dict:
    raw = event.metadata.get("args", {})
    return raw if isinstance(raw, dict) else {}


def _error(event: TraceEvent) -> str:
    return str(event.metadata.get("error", ""))


def _important_args(event: TraceEvent) -> dict:
    args = _args(event)
    keys_by_tool = {
        "fs.read": ("path",),
        "fs.write": ("path",),
        "fs.delete": ("path",),
        "web.open": ("id",),
        "web.search": ("query",),
        "email.read": ("id",),
        "email.send": ("to",),
        "http.post": ("url",),
        "shell.run": ("cmd",),
    }
    keys = keys_by_tool.get(event.name, ())
    return {key: args.get(key) for key in keys}


def matched_prefix_length(desired: Trace, actual: Trace) -> int:
    matched = 0
    for expected, observed in zip(desired.events, actual.events):
        if expected.name != observed.name:
            break
        matched += 1
    return matched


def diagnose(
    desired: Trace,
    actual: Trace,
    predicate_hits: list[JEDPredicateHit] | tuple[JEDPredicateHit, ...],
    *,
    timed_out: bool = False,
    parser_invalid: bool = False,
) -> FailureDiagnosis:
    desired_steps = len(desired.events)
    actual_steps = len(actual.events)
    matched = matched_prefix_length(desired, actual)
    denominator = max(1, desired_steps)
    progress = min(1.0, matched / denominator)

    if timed_out:
        return FailureDiagnosis(
            FailureStage.TIMEOUT, matched, desired_steps, actual_steps, progress, "replay deadline"
        )
    if parser_invalid:
        return FailureDiagnosis(
            FailureStage.PARSER_INVALID,
            matched,
            desired_steps,
            actual_steps,
            progress,
            "model output could not be parsed into the expected tool action",
        )
    if desired_steps and actual_steps == 0:
        return FailureDiagnosis(
            FailureStage.NO_TOOL, matched, desired_steps, actual_steps, 0.0, "no tool call observed"
        )

    for index, observed in enumerate(actual.events):
        if not observed.ok:
            error = _error(observed)
            if error.startswith("denied:") or error.startswith("confirm_required:"):
                return FailureDiagnosis(
                    FailureStage.GUARDRAIL_DENIED,
                    min(matched, index),
                    desired_steps,
                    actual_steps,
                    min(1.0, index / denominator),
                    error,
                )
            return FailureDiagnosis(
                FailureStage.TOOL_ERROR,
                min(matched, index),
                desired_steps,
                actual_steps,
                min(1.0, index / denominator),
                error or "tool call failed",
            )

    for expected, observed in zip(desired.events, actual.events):
        if expected.name != observed.name:
            return FailureDiagnosis(
                FailureStage.WRONG_TOOL,
                matched,
                desired_steps,
                actual_steps,
                progress,
                f"expected {expected.name}, observed {observed.name}",
            )
        expected_args = _important_args(expected)
        observed_args = _important_args(observed)
        if expected_args and expected_args != observed_args:
            return FailureDiagnosis(
                FailureStage.WRONG_ARGS,
                matched,
                desired_steps,
                actual_steps,
                progress,
                f"important args differ for {expected.name}",
            )

    if actual_steps < desired_steps:
        return FailureDiagnosis(
            FailureStage.PARTIAL_CHAIN,
            matched,
            desired_steps,
            actual_steps,
            progress,
            "replay stopped before desired abstract trace completed",
        )
    if not predicate_hits:
        return FailureDiagnosis(
            FailureStage.PREDICATE_MISS,
            matched,
            desired_steps,
            actual_steps,
            progress,
            "desired actions executed but no canonical predicate fired",
        )
    return FailureDiagnosis(
        FailureStage.SUCCESS,
        matched,
        desired_steps,
        actual_steps,
        1.0,
        "canonical predicate fired",
    )
