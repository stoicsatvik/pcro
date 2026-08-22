"""Progress-aware curriculum and reward shaping for abstract trace learning."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .failure_taxonomy import FailureDiagnosis, FailureStage


@dataclass(frozen=True)
class CurriculumSignal:
    shaped_reward: float
    priority: float
    focus: str


STAGE_PENALTY = {
    FailureStage.TIMEOUT: 0.8,
    FailureStage.PARSER_INVALID: 0.7,
    FailureStage.NO_TOOL: 0.6,
    FailureStage.WRONG_TOOL: 0.45,
    FailureStage.WRONG_ARGS: 0.35,
    FailureStage.GUARDRAIL_DENIED: 0.5,
    FailureStage.TOOL_ERROR: 0.4,
    FailureStage.PARTIAL_CHAIN: 0.2,
    FailureStage.PREDICATE_MISS: 0.1,
    FailureStage.SUCCESS: 0.0,
}


def signal(
    diagnosis: FailureDiagnosis,
    *,
    canonical_reward: float = 0.0,
    semantic_validity: float = 0.0,
) -> CurriculumSignal:
    canonical_component = min(1.0, max(0.0, canonical_reward) / 64.0)
    semantic_component = min(1.0, max(0.0, semantic_validity))
    progress_component = diagnosis.progress
    penalty = STAGE_PENALTY[diagnosis.stage]
    shaped = (
        0.55 * canonical_component
        + 0.25 * progress_component
        + 0.20 * semantic_component
        - penalty
    )
    priority = max(0.0, 1.0 - diagnosis.progress) + penalty
    return CurriculumSignal(
        shaped_reward=shaped,
        priority=priority,
        focus=diagnosis.stage.value,
    )


class CurriculumTracker:
    def __init__(self) -> None:
        self.failures: Counter[FailureStage] = Counter()
        self.successes = 0

    def observe(self, diagnosis: FailureDiagnosis) -> None:
        if diagnosis.stage == FailureStage.SUCCESS:
            self.successes += 1
        else:
            self.failures[diagnosis.stage] += 1

    def next_focus(self) -> str:
        if not self.failures:
            return "collect_more_replays"
        stage, _ = self.failures.most_common(1)[0]
        return stage.value

    def snapshot(self) -> dict[str, int | str]:
        return {
            "successes": self.successes,
            "next_focus": self.next_focus(),
            **{stage.value: count for stage, count in self.failures.items()},
        }
