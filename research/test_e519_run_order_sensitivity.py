from pathlib import Path

import numpy as np
import pytest

from research.e519_run_order_sensitivity import (
    SensitivityError,
    analyze,
    run,
)

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
TRACES = RESULTS / "e516_cpu_stress_holdout_traces.csv"
CATALOG = RESULTS / "e516_cpu_stress_catalog.csv"
PROVENANCE = RESULTS / "e516_cpu_stress_provenance.json"


def test_pinned_trace_reproduces_e518_and_survives_task_and_position_sensitivity():
    result = run(TRACES, CATALOG, PROVENANCE)
    assert result["cohort"] == {"runs": 6, "tasks_per_run": 24, "observations": 144}
    assert result["primary_reproduction"]["e518_log_duration_slope"] == pytest.approx(
        -0.0523642835, abs=1e-8
    )
    assert result["leave_one_task_out"]["task_count"] == 24
    assert result["leave_one_task_out"]["all_slopes_negative"] is True
    assert result["leave_one_task_out"]["minimum_slope"] == pytest.approx(-0.0628174805, abs=1e-8)
    assert result["leave_one_task_out"]["maximum_slope"] == pytest.approx(-0.0458898754, abs=1e-8)
    assert result["position_trimming"]["all_slopes_negative"] is True
    assert result["position_trimming"]["minimum_slope"] == pytest.approx(-0.0936237279, abs=1e-8)
    assert result["position_trimming"]["maximum_slope"] == pytest.approx(-0.0617474971, abs=1e-8)
    assert result["source"]["trace_sha256"] == (
        "e00881175d3294a5f03a1cce090015047e955847955e195142403249f975ff7d"
    )


def test_rank_sensitivity_is_deterministic_and_kept_exploratory():
    first = run(TRACES, CATALOG, PROVENANCE, permutations=999, seed=20261112)
    second = run(TRACES, CATALOG, PROVENANCE, permutations=999, seed=20261112)
    a = first["within_task_rank_sensitivity"]
    b = second["within_task_rank_sensitivity"]
    assert a == b
    assert a["rank_slope_per_full_run"] < 0
    assert 0 < a["within_run_permutation_p"] <= 1
    assert "not independent confirmation" in a["interpretation"]


def test_frozen_run_specific_heterogeneity_is_preserved():
    result = run(TRACES, CATALOG, PROVENANCE, permutations=999)
    signs = result["run_slope_signs"]
    assert signs == {"negative": 5, "positive": 1, "zero": 0}
    assert result["claim_boundary"]["causal_mechanism"] == "NOT IDENTIFIED"
    assert result["claim_boundary"]["independent_host_replication"] == "NOT MEASURED"


def test_analyze_rejects_wrong_panel_shape_and_nonfinite_values():
    with pytest.raises(SensitivityError, match="frozen"):
        analyze(np.ones((5, 24)), np.ones((5, 24)))
    bad = np.ones((6, 24))
    bad[0, 0] = np.nan
    with pytest.raises(SensitivityError, match="finite"):
        analyze(bad, np.tile(np.linspace(0, 1, 24), (6, 1)))
