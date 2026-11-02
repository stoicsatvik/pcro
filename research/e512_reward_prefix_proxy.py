"""E512: preregistered independent-draw reward-prefix ranking diagnostic.

Synthetic E507 fixtures only. No fitted policies, empirical latency, or evaluator access.
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
from research.e511_heldout_tail_proxy import completes, sign

START, END = 1056, 1087
DRAWS = 128
Q = 0.55
POLICY_A, POLICY_B = "dp50", "exact400"
DIAGNOSTIC_STREAM = 0xE512A000
OUTCOME_STREAM = 0xE512B000


def completed_prefix_reward(rows, ids, factors):
    """Reward accrued before first budget violation; deliberately omits penalty."""
    cost = reward = 0.0
    for idx in ids:
        _, task_reward, nominal_cost = rows[idx]
        if cost + nominal_cost * factors[idx] > BUDGET:
            break
        cost += nominal_cost * factors[idx]
        reward += task_reward
    return reward


def _scenarios(rng, n_tasks, draws):
    for _ in range(draws):
        common = rng.gauss(0, 1)
        independent = [rng.gauss(0, 1) for _ in range(n_tasks)]
        yield {
            "gaussian": [(1.0, gaussian_factors(common, independent, Q))],
            "bernoulli": [
                (1.0 - Q, gaussian_factors(common, independent, 0.0)),
                (Q, gaussian_factors(common, independent, 1.0)),
            ],
        }


def evaluate(start=START, end=END, draws=DRAWS):
    if draws <= 0 or end < start:
        raise ValueError("nonempty seed cohort and positive draw count required")
    per_seed = []
    for seed in range(start, end + 1):
        rows = fixture(seed)
        chosen = policies(rows)
        ids_a, ids_b = chosen[POLICY_A], chosen[POLICY_B]
        totals = {
            family: {"reward_prefix_gap": 0.0, "completion_gap": 0.0,
                     "utility_gap": 0.0}
            for family in ("gaussian", "bernoulli")
        }
        diagnostic_rng = random.Random(DIAGNOSTIC_STREAM ^ seed)
        outcome_rng = random.Random(OUTCOME_STREAM ^ seed)
        for scenario in _scenarios(diagnostic_rng, len(rows), draws):
            for family, weighted_factors in scenario.items():
                for weight, factors in weighted_factors:
                    totals[family]["reward_prefix_gap"] += weight * (
                        completed_prefix_reward(rows, ids_a, factors)
                        - completed_prefix_reward(rows, ids_b, factors)
                    )
                    totals[family]["completion_gap"] += weight * (
                        int(completes(rows, ids_a, factors))
                        - int(completes(rows, ids_b, factors))
                    )
        for scenario in _scenarios(outcome_rng, len(rows), draws):
            for family, weighted_factors in scenario.items():
                for weight, factors in weighted_factors:
                    totals[family]["utility_gap"] += weight * (
                        realized(rows, ids_a, factors)
                        - realized(rows, ids_b, factors)
                    )
        per_seed.append({
            "seed": seed,
            **{
                family: {metric: value / draws for metric, value in totals[family].items()}
                for family in totals
            },
        })

    summary = {}
    for family in ("gaussian", "bernoulli"):
        rows = [entry[family] for entry in per_seed]
        utility_signs = [sign(entry["utility_gap"]) for entry in rows]
        family_result = {
            "seed_count": len(rows),
            "mean_utility_gap": round(mean(entry["utility_gap"] for entry in rows), 6),
        }
        for proxy in ("reward_prefix", "completion"):
            key = f"{proxy}_gap"
            prediction = [sign(entry[key]) for entry in rows]
            agreement = sum(
                p == actual and p != 0
                for p, actual in zip(prediction, utility_signs)
            )
            family_result[proxy] = {
                "mean_gap": round(mean(entry[key] for entry in rows), 6),
                "sign_agreement": agreement,
                "sign_disagreement": sum(
                    p != actual and p != 0 and actual != 0
                    for p, actual in zip(prediction, utility_signs)
                ),
                "proxy_ties": sum(p == 0 for p in prediction),
                "utility_ties": sum(actual == 0 for actual in utility_signs),
            }
        family_result["passes_75pct_and_baseline_improvement_gate"] = (
            family_result["reward_prefix"]["sign_agreement"] >= 0.75 * len(rows)
            and family_result["reward_prefix"]["sign_agreement"]
            > family_result["completion"]["sign_agreement"]
        )
        summary[family] = family_result

    return {
        "experiment": "E512_INDEPENDENT_REWARD_PREFIX",
        "seed_cohort": [start, end],
        "diagnostic_draws_per_seed": draws,
        "outcome_draws_per_seed": draws,
        "independent_rng_streams": [hex(DIAGNOSTIC_STREAM), hex(OUTCOME_STREAM)],
        "target_pairwise_pearson_q": Q,
        "policy_comparison": f"{POLICY_A} minus {POLICY_B}",
        "summary": summary,
        "per_seed": per_seed,
        "limitations": (
            "Synthetic E507 fixtures, no measured latency. Prefix reward is related "
            "algebraically to realized utility but omits failure penalty. Diagnostic "
            "and outcome draws are independent, with shared model assumptions."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
