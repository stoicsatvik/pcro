"""Pinned source snapshot plus hosted-evaluator facts used by PCRO."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class BenchmarkManifest:
    sdk_source_commit: str
    source_snapshot_label: str
    hosted_update_date: str
    hosted_models: tuple[str, ...]
    public_guardrail: str
    private_guardrail_known: bool
    max_findings: int
    max_messages_per_finding: int
    default_tool_hops: int
    current_advertised_attack_budget_seconds_per_model: int | None
    notes: tuple[str, ...]


CURRENT = BenchmarkManifest(
    sdk_source_commit="30c769419a09f3dc64d5606a0a097b8a2a61c110",
    source_snapshot_label="public SDK source inspected by PCRO",
    hosted_update_date="2026-08-19",
    hosted_models=("gpt_oss", "gemma_4"),
    public_guardrail="optimal_public",
    private_guardrail_known=False,
    max_findings=2_000,
    max_messages_per_finding=32,
    default_tool_hops=4,
    current_advertised_attack_budget_seconds_per_model=18_000,
    notes=(
        "Hosted evaluator may evolve after the pinned source snapshot.",
        "Runtime budgets must remain configurable rather than embedded in planners.",
        "Private guardrail behavior is intentionally not inferred as fact.",
        "The August evaluator update improved Gemma tool-call normalization and partial replay scoring.",
    ),
)


def manifest_dict() -> dict:
    return asdict(CURRENT)
