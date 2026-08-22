from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .hardlab import run_hardlab
from .jed_contract import (
    ATTACK_ELITE_RAW,
    DEFAULT_MAX_TOOL_HOPS,
    MAX_REPLAY_FINDINGS,
    MAX_REPLAY_MESSAGES_PER_FINDING,
    SEVERITY_WEIGHT,
)
from .model import Trace
from .planner import rank_traces, select_under_budget
from .reachability import public_u2a_certificate
from .synthetic import generate_traces


def _load(path: str) -> list[Trace]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("trace file must contain a JSON list")
    return [Trace.from_dict(item) for item in payload]


def _synthesize(args: argparse.Namespace) -> None:
    traces = generate_traces(args.count, seed=args.seed)
    Path(args.out).write_text(
        json.dumps([trace.to_dict() for trace in traces], indent=2),
        encoding="utf-8",
    )
    print(f"wrote {len(traces)} synthetic traces to {args.out}")


def _analyze(args: argparse.Namespace) -> None:
    scores = rank_traces(_load(args.path))
    rows = [
        {
            "trace_id": score.trace_id,
            "total_value": score.total_value,
            "predicate_reward": score.predicate_reward,
            "diversity_bonus": score.diversity_bonus,
            "replay_cost_ms": score.replay_cost_ms,
            "density_per_second": round(score.density_per_second, 3),
            "hits": [hit.name for hit in score.hits],
        }
        for score in scores
    ]
    print(json.dumps(rows, indent=2))


def _optimize(args: argparse.Namespace) -> None:
    portfolio = select_under_budget(_load(args.path), args.budget_ms)
    result = {
        "budget_ms": args.budget_ms,
        "total_cost_ms": portfolio.total_cost_ms,
        "total_value": portfolio.total_value,
        "selected": [score.trace_id for score in portfolio.selected],
    }
    print(json.dumps(result, indent=2))


def _hardlab(args: argparse.Namespace) -> None:
    print(json.dumps(run_hardlab(max_events=args.max_events, top=args.top), indent=2))


def _contract(_: argparse.Namespace) -> None:
    result = {
        "severity_weight": SEVERITY_WEIGHT,
        "attack_elite_raw": ATTACK_ELITE_RAW,
        "max_replay_findings": MAX_REPLAY_FINDINGS,
        "max_messages_per_finding": MAX_REPLAY_MESSAGES_PER_FINDING,
        "default_max_tool_hops": DEFAULT_MAX_TOOL_HOPS,
        "public_u2a_reachability": asdict(public_u2a_certificate()),
    }
    print(json.dumps(result, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pcro")
    sub = parser.add_subparsers(dest="command", required=True)

    synth = sub.add_parser("synthesize", help="generate deterministic synthetic traces")
    synth.add_argument("--count", type=int, default=20)
    synth.add_argument("--seed", type=int, default=7)
    synth.add_argument("--out", default="traces.json")
    synth.set_defaults(func=_synthesize)

    analyze = sub.add_parser("analyze", help="score and rank a JSON trace corpus")
    analyze.add_argument("path")
    analyze.set_defaults(func=_analyze)

    optimize = sub.add_parser("optimize", help="select a portfolio under replay budget")
    optimize.add_argument("path")
    optimize.add_argument("--budget-ms", type=int, required=True)
    optimize.set_defaults(func=_optimize)

    hardlab = sub.add_parser("hardlab", help="run abstract evaluator/guardrail hard tests")
    hardlab.add_argument("--max-events", type=int, default=3, choices=range(1, 6))
    hardlab.add_argument("--top", type=int, default=20)
    hardlab.set_defaults(func=_hardlab)

    contract = sub.add_parser("contract", help="print the pinned public benchmark contract")
    contract.set_defaults(func=_contract)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
