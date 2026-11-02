"""E511: held-out 24-task test of a simple completion-tail ranking proxy.

Diagnostic only. This is not a calibrated predictor or real replay latency.
The policy selections are frozen by E507; no policy or threshold is optimized.
"""
import json
import random
from statistics import mean

from research.e507_gaussian_copula import (
    BUDGET,
    fixture,
    gaussian_factors,
    policies,
    realized,
)

START, END = 1024, 1055
DRAWS = 128
Q = 0.55
POLICY_A, POLICY_B = "dp50", "exact400"


def completes(rows, ids, factors):
    """Positive latencies make total selected cost <= budget equivalent to completion."""
    return sum(rows[idx][2] * factors[idx] for idx in ids) <= BUDGET


def sign(value, eps=1e-9):
    return (value > eps) - (value < -eps)


def evaluate(start=START, end=END, draws=DRAWS):
    """Paired, seed-level out-of-sample comparison with no fitted parameters."""
    if draws <= 0 or end < start:
        raise ValueError("nonempty seed cohort and positive draw count required")
    per_seed = []
    for seed in range(start, end + 1):
        rows = fixture(seed)
        selected = policies(rows)
        ids_a, ids_b = selected[POLICY_A], selected[POLICY_B]
        sums = {family: {"utility_gap": 0.0, "completion_gap": 0.0}
                for family in ("gaussian", "bernoulli")}
        rng = random.Random(0xE5110000 ^ seed)
        for _ in range(draws):
            common = rng.gauss(0, 1)
            independent = [rng.gauss(0, 1) for _ in rows]
            scenarios = {
                "gaussian": [(1.0, gaussian_factors(common, independent, Q))],
                "bernoulli": [
                    (1.0 - Q, gaussian_factors(common, independent, 0.0)),
                    (Q, gaussian_factors(common, independent, 1.0)),
                ],
            }
            for family, weighted_factors in scenarios.items():
                for weight, factors in weighted_factors:
                    sums[family]["utility_gap"] += weight * (
                        realized(rows, ids_a, factors) - realized(rows, ids_b, factors)
                    )
                    sums[family]["completion_gap"] += weight * (
                        int(completes(rows, ids_a, factors))
                        - int(completes(rows, ids_b, factors))
                    )
        per_seed.append({
            "seed": seed,
            **{family: {metric: value / draws for metric, value in totals.items()}
               for family, totals in sums.items()},
        })
    summary = {}
    for family in ("gaussian", "bernoulli"):
        utility = [r[family]["utility_gap"] for r in per_seed]
        completion = [r[family]["completion_gap"] for r in per_seed]
        signs = [(sign(c), sign(u)) for c, u in zip(completion, utility)]
        # A tie is not counted as a successful directional prediction.
        summary[family] = {
            "mean_utility_gap": round(mean(utility), 6),
            "mean_completion_gap": round(mean(completion), 6),
            "sign_agreement": sum(a == b and a != 0 for a, b in signs),
            "sign_disagreement": sum(a != b and a != 0 and b != 0 for a, b in signs),
            "proxy_ties": sum(a == 0 for a, _ in signs),
            "utility_ties": sum(b == 0 for _, b in signs),
            "seed_count": len(signs),
        }
        summary[family]["passes_predeclared_75pct_direction_gate"] = (
            summary[family]["sign_agreement"] >= 0.75 * len(signs)
        )
    return {
        "experiment": "E511_HELDOUT_COMPLETION_TAIL_PROXY",
        "seed_cohort": [start, end],
        "draws_per_seed": draws,
        "target_pairwise_pearson_q": Q,
        "policy_comparison": f"{POLICY_A} minus {POLICY_B}",
        "summary": summary,
        "per_seed": per_seed,
        "limitations": (
            "Synthetic E507 latency laws, no empirical replay, no fitted prediction; "
            "same simulated draws evaluate completion and utility. Sign proxy ignores "
            "reward magnitudes and failure position. Descriptive seed counts only."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
