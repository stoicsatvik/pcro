from pcro.model import Trace, TraceEvent
from pcro.semantic_validity import semantic_evidence


def test_multistep_chain_gets_more_semantic_evidence_than_isolated_effect():
    isolated = Trace(
        "isolated",
        (TraceEvent("email.send", source="tool", side_effect="SHARE", scope="external"),),
    )
    chain = Trace(
        "chain",
        (
            TraceEvent("web.open", source="web", side_effect="NETWORK", scope="public"),
            TraceEvent("email.send", source="tool", side_effect="SHARE", scope="external"),
        ),
    )
    assert semantic_evidence(chain).score > semantic_evidence(isolated).score
    assert "untrusted_to_privileged_chain" in semantic_evidence(chain).labels
