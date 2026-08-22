from pcro.jed_contract import eval_jed_predicates, raw_predicate_reward
from pcro.model import Trace, TraceEvent
from pcro.semantics_lab import (
    enumerate_short_skeletons,
    rank_skeletons,
    temporal_intent_ablation,
)


def test_temporal_intent_tail_changes_prior_share_classification():
    trace = Trace(
        "temporal",
        (
            TraceEvent("web.open", source="web", side_effect="READ"),
            TraceEvent("email.send", source="tool", side_effect="SHARE"),
        ),
        ("check the fixture", "review outcome"),
    )
    base = raw_predicate_reward(eval_jed_predicates(trace))
    results = {result.name: result for result in temporal_intent_ablation(trace)}
    assert base == 20
    assert results["share_authorized_tail"].variant_reward == 0
    assert results["share_authorized_tail"].delta == -20


def test_enumerator_finds_nonzero_density_traces():
    ranked = rank_skeletons(enumerate_short_skeletons(max_events=2))
    assert ranked
    assert ranked[0][0] > 0
