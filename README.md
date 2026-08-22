# PCRO

**Predicate-Compiled Replay Optimisation** — a local research framework for studying replay-based security evaluators for tool-using AI agents.

PCRO treats an evaluator as an explicit optimisation problem: represent traces, evaluate benchmark predicates, measure reward/cost, generate synthetic traces, and rank candidate traces under replay budgets.

> This repository is scoped to controlled, local, and benchmark environments. It does not automate attacks against third-party systems or bypass real-world access controls.

## Research questions

- How should replay-validated predicate reward be modelled?
- Which synthetic trace structures produce high predicate density per unit replay cost?
- How sensitive are evaluator semantics to event ordering and trace length?
- How can near-miss traces be recorded so failed experiments improve future search?
- How robust is a candidate portfolio across different simulated guardrail policies?

## Initial architecture

```text
pcro/
  cli.py                 command-line interface
  model.py               trace/event data model
  predicates.py          predicate specification + evaluator
  scoring.py             reward, density, and replay-cost objective
  synthetic.py           deterministic synthetic trace generator
  planner.py             budget-aware trace ranking
  experiments.py         JSONL experiment store + failure records

tests/
  test_predicates.py
  test_scoring.py
  test_planner.py
```

## Quick start

```bash
python -m pip install -e '.[dev]'
pcro synthesize --count 12 --out traces.json
pcro analyze traces.json
pcro optimize traces.json --budget-ms 2500
pytest
```

## Core objective

For a replayed trace `τ`, PCRO tracks a simple research objective:

```text
value(τ) = weighted_predicate_reward(τ) + diversity_bonus(τ)
density(τ) = value(τ) / replay_cost(τ)
```

The implementation deliberately keeps predicate definitions explicit and testable. Benchmark-specific evaluator rules can be added as isolated predicate specifications rather than hidden inside prompt-generation code.

## Status

`v0`: scorer-semantics laboratory + synthetic traces + budget-aware optimiser.
