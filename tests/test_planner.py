from pcro.model import Trace, TraceEvent
from pcro.planner import select_under_budget


def test_budget_is_respected() -> None:
    traces = [
        Trace(
            f"t-{index}",
            events=(TraceEvent("record", side_effect="WRITE", latency_ms=100),),
            cell=f"c-{index}",
        )
        for index in range(5)
    ]
    portfolio = select_under_budget(traces, budget_ms=250)
    assert portfolio.total_cost_ms <= 250
    assert len(portfolio.selected) == 2


def test_negative_budget_rejected() -> None:
    try:
        select_under_budget([], -1)
    except ValueError as exc:
        assert "non-negative" in str(exc)
    else:
        raise AssertionError("negative budget should fail")
