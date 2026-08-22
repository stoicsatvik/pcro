from pcro.properties import run_property_suite


def test_metamorphic_property_suite():
    result = run_property_suite(100)
    assert result["passed"], result
