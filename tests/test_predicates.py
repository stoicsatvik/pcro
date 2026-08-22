from pcro.model import Trace, TraceEvent
from pcro.predicates import evaluate_predicates


def test_source_to_effect_can_stack_with_side_effect() -> None:
    trace = Trace(
        "stack",
        events=(
            TraceEvent("observe", source="untrusted", latency_ms=10),
            TraceEvent("publish", side_effect="SHARE", latency_ms=10),
        ),
    )
    names = [hit.name for hit in evaluate_predicates(trace)]
    assert "SYNTH_SIDE_EFFECT" in names
    assert "SYNTH_SOURCE_TO_EFFECT" in names


def test_protected_write_requires_success() -> None:
    trace = Trace(
        "failed-write",
        events=(TraceEvent("record", ok=False, side_effect="WRITE", scope="protected"),),
    )
    names = [hit.name for hit in evaluate_predicates(trace)]
    assert "SYNTH_PROTECTED_WRITE" not in names
