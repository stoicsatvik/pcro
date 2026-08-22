"""Model-conditioned empirical profiles.

No hosted-model latency or success number is hard-coded as fact. Profiles start with weak priors
and are updated from local/public benchmark replays, keeping GPT-OSS and Gemma observations apart.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .bandit import Arm
from .runtime import RunningStats


@dataclass
class FamilyProfile:
    family: str
    success: Arm = field(init=False)
    latency: RunningStats = field(default_factory=RunningStats)
    parser_failures: int = 0
    tool_failures: int = 0
    predicate_misses: int = 0

    def __post_init__(self) -> None:
        self.success = Arm(self.family, reward_if_success=1.0, expected_cost_ms=1000.0)

    def observe(
        self,
        *,
        succeeded: bool,
        latency_ms: float,
        failure_stage: str | None = None,
    ) -> None:
        self.success.observe(succeeded, latency_ms)
        self.latency.observe(latency_ms)
        if failure_stage == "parser_invalid":
            self.parser_failures += 1
        elif failure_stage in {"wrong_tool", "wrong_args", "guardrail_denied", "tool_error"}:
            self.tool_failures += 1
        elif failure_stage in {"predicate_miss", "no_predicate"}:
            self.predicate_misses += 1


@dataclass
class ModelProfile:
    model: str
    families: dict[str, FamilyProfile] = field(default_factory=dict)

    def family(self, family: str) -> FamilyProfile:
        if family not in self.families:
            self.families[family] = FamilyProfile(family)
        return self.families[family]

    def observe(
        self,
        family: str,
        *,
        succeeded: bool,
        latency_ms: float,
        failure_stage: str | None = None,
    ) -> None:
        self.family(family).observe(
            succeeded=succeeded,
            latency_ms=latency_ms,
            failure_stage=failure_stage,
        )


class ModelRegistry:
    def __init__(self) -> None:
        self._profiles: dict[str, ModelProfile] = {}

    def profile(self, model: str) -> ModelProfile:
        key = model.strip().lower()
        if not key:
            raise ValueError("model name cannot be empty")
        if key not in self._profiles:
            self._profiles[key] = ModelProfile(key)
        return self._profiles[key]

    def observe(
        self,
        model: str,
        family: str,
        *,
        succeeded: bool,
        latency_ms: float,
        failure_stage: str | None = None,
    ) -> None:
        self.profile(model).observe(
            family,
            succeeded=succeeded,
            latency_ms=latency_ms,
            failure_stage=failure_stage,
        )
