from pcro.model import Trace, TraceEvent
from pcro.parity import trace_mapping


def test_trace_mapping_preserves_contract_fields():
    trace = Trace(
        "x",
        (
            TraceEvent(
                "http.post",
                ok=False,
                source="web",
                side_effect="SHARE",
                scope="external",
                metadata={
                    "args": {"url": "https://benchmark.invalid", "data": "x"},
                    "output": "",
                    "error": "denied:test",
                },
            ),
        ),
        ("review benchmark",),
    )
    mapping = trace_mapping(trace)
    event = mapping["tool_events"][0]
    assert event["name"] == "http.post"
    assert event["args"]["data"] == "x"
    assert event["error"] == "denied:test"
    assert mapping["user_messages"] == ["review benchmark"]
