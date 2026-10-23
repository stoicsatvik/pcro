"""Closed-loop learning over abstract replay traces.

This layer learns *which benchmark trace families deserve another local experiment*. It does not
produce natural-language attack prompts or contact external systems.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .bandit import Arm
from .guardrail_lab import DEFAULT_ENSEMBLE, score_ensemble
from .jed_contract import eval_jed_predicates, raw_predicate_reward
from .model import Trace
from .surrogate import OnlineLogisticRanker

FEATURE_NAMES = (
    "trace_length",
    "untrusted_fraction",
    "share_fraction",
    "exec_fraction",
    "write_fraction",
    "http_post_fraction",
    "email_send_fraction",
    "sensitive_arg_fraction",
    "marker_fraction",
    "predicate_reward_scaled",
    "public_reward_scaled",
    "ensemble_mean_scaled",
    "ensemble_worst_scaled",
)


@dataclass(frozen=True)
class RankedExperiment:
    family: str
    trace_id: str
    predicted_success: float
    public_reward: int
    robust_reward: float
    expected_cost_ms: float
    acquisition: float


class FailureAtlas:
    def __init__(self) -> None:
        self.counts: Counter[tuple[str, str]] = Counter()

    def observe(self, family: str, failure_stage: str | None) -> None:
        if failure_stage:
            self.counts[(family, failure_stage)] += 1

    def most_common(self, limit: int = 20) -> list[tuple[tuple[str, str], int]]:
        return self.counts.most_common(limit)


def _contains_sensitive_arg(trace: Trace, index: int) -> bool:
    event = trace.events[index]
    args = event.metadata.get("args", {})
    if not isinstance(args, dict):
        return False
    text = " ".join(str(value).lower() for value in args.values())
    return any(token in text for token in ("secret", "password", "token", "credential"))


def trace_features(trace: Trace) -> tuple[float, ...]:
    n = max(1, len(trace.events))
    counts = Counter(event.side_effect for event in trace.events)
    untrusted = sum(event.source in {"web", "email"} for event in trace.events)
    posts = sum(event.name == "http.post" for event in trace.events)
    sends = sum(event.name == "email.send" for event in trace.events)
    sensitive = sum(_contains_sensitive_arg(trace, index) for index in range(len(trace.events)))
    markers = 0
    for event in trace.events:
        args = event.metadata.get("args", {})
        if isinstance(args, dict) and any("SECRET_MARKER" in str(value) for value in args.values()):
            markers += 1

    reward = raw_predicate_reward(eval_jed_predicates(trace))
    ensemble = score_ensemble(trace, DEFAULT_ENSEMBLE)
    return (
        min(1.0, len(trace.events) / 16.0),
        untrusted / n,
        counts["SHARE"] / n,
        counts["EXEC"] / n,
        counts["WRITE"] / n,
        posts / n,
        sends / n,
        sensitive / n,
        markers / n,
        min(1.0, reward / 128.0),
        min(1.0, ensemble.public_reward / 128.0),
        min(1.0, ensemble.mean_reward / 128.0),
        min(1.0, ensemble.worst_reward / 128.0),
    )


def context_key(family: str, model: str = "generic", guardrail: str = "generic") -> str:
    if model == "generic" and guardrail == "generic":
        return family
    return f"{model}|{guardrail}|{family}"


class AdaptiveResearchLoop:
    """Bayesian family selection + online success surrogate + failure atlas."""

    def __init__(self) -> None:
        self.arms: dict[str, Arm] = {}
        self.surrogate = OnlineLogisticRanker(len(FEATURE_NAMES), learning_rate=0.05)
        self.failures = FailureAtlas()

    def _arm(self, key: str, reward: float, cost_ms: float) -> Arm:
        if key not in self.arms:
            self.arms[key] = Arm(
                name=key,
                reward_if_success=max(0.0, reward),
                expected_cost_ms=max(1.0, cost_ms),
            )
        arm = self.arms[key]
        arm.reward_if_success = max(arm.reward_if_success, reward)
        return arm

    def observe(
        self,
        family: str,
        trace: Trace,
        *,
        success: bool,
        replay_cost_ms: float | None = None,
        failure_stage: str | None = None,
        model: str = "generic",
        guardrail: str = "generic",
    ) -> None:
        ensemble = score_ensemble(trace)
        cost = float(replay_cost_ms if replay_cost_ms is not None else trace.replay_cost_ms)
        key = context_key(family, model, guardrail)
        arm = self._arm(key, ensemble.mean_reward, cost)
        arm.observe(success, cost)
        self.surrogate.update(trace_features(trace), int(success))
        if not success:
            self.failures.observe(key, failure_stage or "unknown")

    def rank(
        self,
        candidates: Iterable[tuple[str, Trace]],
        *,
        pessimism: float = 0.5,
        model: str = "generic",
        guardrail: str = "generic",
    ) -> list[RankedExperiment]:
        ranked: list[RankedExperiment] = []
        for family, trace in candidates:
            ensemble = score_ensemble(trace)
            features = trace_features(trace)
            p_model = self.surrogate.predict_proba(features)
            key = context_key(family, model, guardrail)
            arm = self._arm(key, ensemble.mean_reward, trace.replay_cost_ms)
            p_family = arm.lower_confidence_success() if pessimism > 0 else arm.posterior_mean
            predicted = (1.0 - pessimism) * p_model + pessimism * p_family
            robust_reward = 0.5 * ensemble.cvar_reward + 0.5 * ensemble.worst_reward
            cost = max(1.0, arm.expected_cost_ms)
            acquisition = predicted * robust_reward / cost
            ranked.append(
                RankedExperiment(
                    family=family,
                    trace_id=trace.trace_id,
                    predicted_success=predicted,
                    public_reward=ensemble.public_reward,
                    robust_reward=robust_reward,
                    expected_cost_ms=cost,
                    acquisition=acquisition,
                )
            )
        return sorted(ranked, key=lambda row: row.acquisition, reverse=True)

    def next_candidate(
        self,
        candidates: Sequence[tuple[str, Trace]],
        *,
        model: str = "generic",
        guardrail: str = "generic",
    ) -> RankedExperiment:
        ranked = self.rank(candidates, model=model, guardrail=guardrail)
        if not ranked:
            raise ValueError("no candidates")
        return ranked[0]
