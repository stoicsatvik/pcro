from pcro.curriculum import CurriculumTracker, signal
from pcro.failure_taxonomy import FailureStage, diagnose
from pcro.jed_contract import eval_jed_predicates
from pcro.model import Trace, TraceEvent


def trace(trace_id, *events):
    return Trace(trace_id, tuple(events), ("review benchmark",))


def test_guardrail_denial_has_specific_stage():
    desired = trace(
        "desired",
        TraceEvent("web.open", source="web", side_effect="NETWORK"),
        TraceEvent("email.send", source="tool", side_effect="SHARE"),
    )
    actual = trace(
        "actual",
        TraceEvent("web.open", source="web", side_effect="NETWORK"),
        TraceEvent(
            "email.send",
            ok=False,
            source="web",
            side_effect="SHARE",
            metadata={"error": "denied:recent_untrusted_source"},
        ),
    )
    diagnosis = diagnose(desired, actual, [])
    assert diagnosis.stage == FailureStage.GUARDRAIL_DENIED
    assert 0 < diagnosis.progress < 1


def test_predicate_miss_differs_from_partial_chain():
    desired = trace("desired", TraceEvent("fs.read", source="file", side_effect="READ"))
    actual = trace("actual", TraceEvent("fs.read", source="file", side_effect="READ"))
    diagnosis = diagnose(desired, actual, eval_jed_predicates(actual))
    assert diagnosis.stage == FailureStage.PREDICATE_MISS


def test_curriculum_tracks_dominant_failure():
    desired = trace("desired", TraceEvent("email.send", source="tool", side_effect="SHARE"))
    empty = trace("empty")
    tracker = CurriculumTracker()
    for _ in range(4):
        diagnosis = diagnose(desired, empty, [])
        tracker.observe(diagnosis)
    assert tracker.next_focus() == "no_tool"
    shaped = signal(diagnosis, canonical_reward=0, semantic_validity=0)
    assert shaped.shaped_reward < 0
