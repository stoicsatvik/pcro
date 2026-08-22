# PCRO

**Predicate-Compiled Replay Optimisation** is a controlled research framework for studying replay-based security evaluators for tool-using AI agents.

PCRO does not start from prompt generation. It starts from the executable evaluator contract, models which abstract traces can survive replay, measures reward per replay cost, and learns from the resulting empirical corpus.

> Scope: deterministic local/public benchmark environments. The project does not automate attacks against third-party systems or bypass real-world access controls.

## Kaggle submission

The repository now contains a self-contained root [`attack.py`](attack.py) implementing the official `AttackAlgorithm` contract for the **AI Agent Security - Multi-Step Tool Attacks** benchmark.

The submission search currently combines:

- deterministic seed families for the benchmark fixture surface;
- trace-guided sequence mutation rather than one-shot prompt enumeration;
- exact public predicate severity weights during discovery;
- score-cell archiving and replay-cost-aware candidate ranking;
- adaptive UCB allocation toward families that are producing validated findings;
- conservative down-ranking of known public-guardrail taint shapes;
- replay-prefix ordering so high-density findings are returned first if replay time expires.

With the pinned public SDK installed, validate the artifact with:

```bash
aicomp validate redteam attack.py
```

## Why this architecture

The public JED scorer is highly structured: predicate events have exponential severity weights, score-cell novelty is comparatively small, findings are replayed from scratch, replay count/message/tool-hop limits are explicit, and guardrail semantics can make some predicate paths unreachable. Training a neural generator before mirroring those contracts would simply learn simulator mistakes faster.

PCRO therefore follows this stack:

```text
public evaluator source
        ↓
contract mirror + metamorphic tests
        ↓
predicate / guardrail reachability
        ↓
abstract trace enumeration
        ↓
robust guardrail ensemble
        ↓
reward-per-replay-cost ranking
        ↓
empirical replay corpus + failure atlas
        ↓
Bayesian / Thompson experiment scheduling
        ↓
online surrogate
        ↓
optional neural surrogate once data volume justifies it
```

## Current modules

```text
pcro/
  jed_contract.py      public scorer/predicate/score-cell mirror
  guardrail_lab.py     public OptimalGuardrail mirror + synthetic stricter policies
  reachability.py      contract-level reachability certificates
  semantics_lab.py     temporal/order/success metamorphic ablations
  hardlab.py           combinatorial abstract-trace stress tests
  adaptive.py          closed-loop experiment acquisition + failure atlas
  bandit.py            Beta posteriors + Thompson-style scheduling primitives
  rl.py                tabular Q-learning over abstract event states
  surrogate.py         dependency-free online logistic success ranker
  neural.py            optional PyTorch replay-success MLP
  runtime.py           replay-latency uncertainty + partial-timeout-aware ordering
  experiments.py       versioned JSONL empirical corpus
  planner.py           replay-budget portfolio selection
```

## Quick start

```bash
python -m pip install -e '.[dev]'
pcro contract
pcro hardlab --max-events 3 --top 20
pcro synthesize --count 50 --out traces.json
pcro analyze traces.json
pcro optimize traces.json --budget-ms 2500
pytest
```

Optional neural surrogate:

```bash
python -m pip install -e '.[ml]'
```

The neural layer is intentionally downstream of real replay data collection. The default learner remains lightweight and auditable while the dataset is small.

## Core objective

For replayed finding `i` under model `m` and guardrail policy `g`, PCRO approximates:

```text
EV_i(m,g) = P(replay success | i,m,g) * replay-validated reward(i,g)
Density_i  = robust_E_g[EV_i] / conservative_replay_cost_i
```

Candidate ordering matters because the evaluator may preserve only the completed replay prefix when time expires. The runtime model therefore uses latency variance, not only mean latency.

## Research findings

See [`docs/BENCHMARK_FINDINGS.md`](docs/BENCHMARK_FINDINGS.md). Important corrections already encoded in tests include:

- score-driving cells exclude user-message hashes;
- final-message intent affects predicate classification over the whole trace;
- predicates accumulate per qualifying event;
- public guardrail taint and scorer lookback windows create structural reachability constraints;
- public-only implementation behavior is penalized by a synthetic stricter guardrail ensemble.

## Status

`v0.3-dev`: executable benchmark contract laboratory + Kaggle submission adapter + replay-aware adaptive search.
