from pcro.properties import run_property_suite


def test_metamorphic_property_suite():
    result = run_property_suite(100)
    assert result["passed"], result


def test_sdk_error_field_is_string_even_when_absent():
    from pcro.model import TraceEvent
    from pcro.parity import _event_mapping

    empty = TraceEvent("fs.read", metadata={"args": {"path": "readme.txt"}})
    assert _event_mapping(empty)["error"] == ""
    explicit = TraceEvent("fs.read", ok=False, metadata={"error": "synthetic failure"})
    assert _event_mapping(explicit)["error"] == "synthetic failure"
    null = TraceEvent("fs.read", ok=False, metadata={"error": None})
    assert _event_mapping(null)["error"] == ""
