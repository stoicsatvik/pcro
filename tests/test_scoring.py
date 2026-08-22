from pcro.model import Trace, TraceEvent
from pcro.scoring import score_trace


def test_severity_weighting_and_density() -> None:
    trace = Trace(
        "weighted",
        events=(
            TraceEvent("observe", source="untrusted", latency_ms=100),
            TraceEvent("publish", side_effect="SHARE", latency_ms=100),
        ),
        cell="new-cell",
    )
    score = score_trace(trace)
    assert score.predicate_reward == 20
    assert score.diversity_bonus == 2
    assert score.total_value == 22
    assert score.density_per_second == 110


def test_seen_cell_has_no_diversity_bonus() -> None:
    trace = Trace("cell", events=(), cell="same")
    assert score_trace(trace, seen_cells={"same"}).diversity_bonus == 0
