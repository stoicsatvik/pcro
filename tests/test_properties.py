import pytest

from pcro.model import Trace, TraceEvent
from pcro.parity import trace_mapping
from pcro.properties import run_property_suite


def test_metamorphic_property_suite():
    result = run_property_suite(100)
    assert result["passed"], result


@pytest.mark.parametrize(
    ("metadata", "expected_error"),
    [
        ({}, ""),
        ({"error": None}, ""),
        ({"error": "synthetic failure"}, "synthetic failure"),
        ({"error": 42}, ""),
    ],
)
def test_sdk_error_mapping_is_a_string_without_mutating_trace(metadata, expected_error):
    event = TraceEvent("fs.read", ok=False, metadata=metadata.copy())
    mapped = trace_mapping(Trace("error-contract", (event,)))["tool_events"][0]

    assert mapped["error"] == expected_error
    assert isinstance(mapped["error"], str)
    assert event.metadata == metadata
