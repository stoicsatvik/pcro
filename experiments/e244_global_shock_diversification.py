"""E244: exact synthetic global-shock stress test for replay-family diversification.

Abstract Bernoulli counts only. No attack traces, third-party systems,
private evaluators, empirical correlation estimates or hidden tests.
"""
from __future__ import annotations

import json
import math
import random
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

# Experiments are standalone scripts, not an installed Python package.
_SPEC = spec_from_file_location("e225_family_diversification",
                                Path(__file__).with_name("e225_family_diversification.py"))
assert _SPEC and _SPEC.loader
_E225 = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_E225)
distribution = _E225.distribution
summary = _E225.summary

PARTITIONS = ((8,), (4, 4), (2, 2, 2, 2), (1,) * 8)
GLOBAL_WEIGHTS = (0.0, 0.01, 0.05, 0.10, 0.25, 0.50, 1.0)


def global_shock_pmf(partition: tuple[int, ...], p: float, strength: float,
                     global_weight: float) -> list[float]:
    """Mixture: family law with probability 1-q; all share G~Bernoulli(p) with q.

    Preserves every candidate's marginal p, but adds unobserved cross-family
    dependence. q is an assumed scenario parameter, not measured frequency.
    """
    if not math.isfinite(global_weight) or not 0 <= global_weight <= 1:
        raise ValueError("global_weight must be finite and in [0,1]")
    base = distribution(partition, p, strength)
    result = [(1-global_weight)*v for v in base]
    result[0] += global_weight*(1-p)
    result[-1] += global_weight*p
    return result


def simulate_global_shock(partition: tuple[int, ...], p: float, strength: float,
                          q: float, trials: int, seed: int) -> list[float]:
    """Independent event-level simulation, not sampling the exact PMF."""
    global_shock_pmf(partition, p, strength, q)  # validation
    if trials < 1:
        raise ValueError("trials must be positive")
    rng = random.Random(seed)
    w = 0.5 / math.sqrt(1+strength)
    counts = [0]*(sum(partition)+1)
    for _ in range(trials):
        if rng.random() < q:
            k = sum(partition)*int(rng.random() < p)
        else:
            k = 0
            for n in partition:
                common = rng.random()
                for _ in range(n):
                    u = common if rng.random() < w else rng.random()
                    k += int(u < p)
        counts[k] += 1
    return [c/trials for c in counts]


def audit(trials: int = 12_000, seed: int = 244025) -> dict:
    rows = []
    for i, q in enumerate(GLOBAL_WEIGHTS):
        for j, partition in enumerate(PARTITIONS):
            exact = global_shock_pmf(partition, 0.5, 0.0, q)
            sampled = simulate_global_shock(partition, 0.5, 0.0, q,
                                            trials, seed + i*17+j)
            s = summary(exact)
            if abs(s["mean_successes"]-4.0) > 1e-10:
                raise AssertionError("Marginal preservation violated")
            error = max(abs(a-b) for a,b in zip(exact,sampled))
            if error >= 0.035:
                raise AssertionError("Independent Monte Carlo disagreement")
            rows.append({"global_shock_weight": q, "family_sizes": list(partition),
                         "exact": s, "max_histogram_error": error})
    clustered_no_global = summary(global_shock_pmf((8,),0.5,0.0,0.0))
    diverse_ten_percent = summary(global_shock_pmf((1,)*8,0.5,0.0,0.1))
    if not (diverse_ten_percent["zero_success_probability"] >
            clustered_no_global["zero_success_probability"]):
        raise AssertionError("Cross-scenario counterexample not reproduced")
    return {
        "schema": "pcro/e244/global-common-shock-synthetic/v1",
        "seed": seed,
        "trials_per_scenario": trials,
        "scenario_count": len(rows),
        "scenarios": rows,
        "counterexample": {
            "clustered_8_no_global_shock": clustered_no_global,
            "diverse_8_with_10pct_global_shock": diverse_ten_percent,
        },
        "claim": "SUPPORTED only for exact synthetic mixture; empirical cross-family replay dependence NOT YET PROVEN",
        "limitations": [
            "The global-shock weight is an analyst-assumed mixture probability, not observed data.",
            "All candidates have equal synthetic Bernoulli marginals and unit reward.",
            "The 10% scenario does not estimate real replay outage or evaluator failure rates.",
            "No attacks, unauthorized testing, hidden evaluation or private data were used.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
