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


def test_missing_and_null_errors_lower_to_sdk_safe_empty_string():
    # The pinned public SDK's cell_signature calls error.startswith(...).
    # A null here crashed randomized parity before any comparison was possible.
    for metadata in ({}, {"error": None}, {"error": ""}):
        trace = Trace("no-error", (TraceEvent("web.open", metadata=metadata),))
        error = trace_mapping(trace)["tool_events"][0]["error"]
        assert error == ""
        assert not error.startswith("denied:")


def test_denial_text_is_preserved_and_nonstring_error_is_explicit():
    for value, expected in (("denied:fixture", "denied:fixture"), (7, "7")):
        trace = Trace("error", (TraceEvent("web.open", ok=False, metadata={"error": value}),))
        mapped = trace_mapping(trace)["tool_events"][0]
        assert mapped["error"] == expected
        assert isinstance(mapped["error"], str)
