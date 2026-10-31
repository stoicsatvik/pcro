# E455 | Falsify risk-neutral expected-prefix superiority under truncation penalties

**31 October 2026.** Isolated synthetic scheduling research. This does not run any evaluator, submit a security finding, or establish production scheduling performance.

## Question and preregistered protocol

E454 improved expected realized prefix reward under a known shared latency multiplier, but about 95% of its schedules truncated. Does the apparent advantage survive when incomplete schedules incur a terminal penalty, and when the latency dependence model is wrong?

Freeze E454's 24-option seeded synthetic generator, 400-unit time budget, density-ordered subsequence restriction, and U[0.7, 1.3) shared multiplier. Use the already-revealed E454 holdout seeds **256–383** only as a development replication, then a new untouched seed range **384–511** as a one-shot holdout from the same generator family. Predeclare fixed policies: nominal exact-400; risk-neutral expected-prefix DP; risk-penalized DP with terminal penalties 50 and 100 reward units; and chance-constrained DPs requiring at least 50% and 90% full-schedule completion under the shared model. No policy is selected or refit using the new holdout.

The exact fully-shared expectation of a fixed schedule is `sum_j reward_j * survival(prefix_nominal_cost_j)`, where `survival(C) = clip((400/C - 0.7)/0.6, 0, 1)`. Completion probability is `survival(total_nominal_cost)`. The penalty-aware DP retains the best prefix reward at each integer cost, then maximizes `expected_prefix_reward - lambda*(1 - completion_probability)`. The chance-constrained DP maximizes expected prefix reward over only those terminal costs whose completion probability meets its threshold. Both are exact **within the frozen density ordering**, not globally optimal permutations.

For dependence misspecification, evaluate the six fixed schedules using 64 deterministic draws per seed under independent, half-shared and fully shared synthetic multipliers, preserving E454's pseudo-random generator. The 128 seeds, not 8,192 draws, are the natural paired units. Half-shared noise changes marginal variance as well as correlation.

## New held-out analytic results (seeds 384–511)

| Fixed policy | Expected prefix reward | P(complete) | Utility, penalty 50 | Utility, penalty 100 |
|---|---:|---:|---:|---:|
| Nominal exact-400 | 624.920 | 0.5300 | 601.419 | 577.918 |
| Risk-neutral DP | **652.252** | 0.0524 | 604.870 | 557.488 |
| Penalty-50 DP | 645.632 | 0.3064 | **610.953** | 576.273 |
| Penalty-100 DP | 617.933 | 0.6692 | 601.395 | **584.856** |
| Chance >= 50% DP | 626.385 | 0.5410 | 603.433 | 580.481 |
| Chance >= 90% DP | 580.442 | 0.9497 | 577.926 | 575.409 |

The risk-neutral DP gains **27.332** reward units over nominal exact but reduces full-schedule completion probability by **47.76 percentage points**. Their exact expected-utility ordering reverses when the terminal penalty exceeds **57.225** reward units. This break-even is a retrospective descriptive crossing for these two frozen policies, not a fitted deployment threshold. The penalty-50 and penalty-100 DPs optimize different explicit objectives, and the preferred policy changes accordingly. High expected prefix reward and high completion probability are competing objectives.

## Independent, half-shared and shared noise stress

64-draw/seed Monte Carlo on the untouched holdout; each cell below is mean `realized_reward - 50*truncation` (synthetic reward units):

| Fixed policy | Fully shared | Half shared | Independent |
|---|---:|---:|---:|
| Nominal exact-400 | 601.08 | 612.75 | 619.54 |
| Risk-neutral DP | 604.61 | 595.28 | 593.42 |
| Penalty-50 DP | **610.48** | 603.82 | 598.40 |
| Penalty-100 DP | 601.52 | **616.33** | 621.48 |
| Chance >= 50% DP | 603.20 | 615.78 | **623.88** |
| Chance >= 90% DP | 578.04 | 583.20 | 583.20 |

At penalty 50, the shared-model penalty-50 DP **fails to transfer** to independent noise: 598.40 versus nominal exact 619.54, a **21.14-unit deficit**. The chance-50 policy does better in that misspecified family (623.88), but this is a retrospective comparison among fixed synthetic policies, not evidence of a universally robust strategy. For penalty 100, the independent-family utility of the penalty-100 DP is 611.38 versus nominal exact 599.55, while risk-neutral DP falls to 543.42.

## Validation and provenance

- `research/e455_truncation_penalty_frontier.mjs` runs with Node.js and no dependencies; `node --check` passed and the full script executed locally.
- **20 exhaustive 8-option checks**: four frozen seeds times three terminal penalties and two chance thresholds. The DP matched brute-force enumeration to 1e-8. Three probability boundary checks, a chance-feasibility check, and a penalty dominance check passed.
- The development population reproduces E454's held-out fully-shared simulated means for exact-400 (**631.677978515625**) and risk-neutral DP (**659.365478515625**) exactly; this is a deterministic regression control, not independent scientific evidence.
- Analytic fully-shared expected rewards and finite-draw Monte Carlo agree approximately on the new holdout, as expected for 64 pseudo-random draws per seed.
- The full machine-readable development/holdout summary is emitted by the script; the pinned compact receipt is in `research/results/e455_truncation_penalty_frontier_20261031.json`. No external dataset or empirical timing measurements were used.

## Claim state and next decisive gate

**SUPPORTED IN A FROZEN SYNTHETIC GENERATOR:** the E454 risk-neutral reward advantage is not invariant to a completion penalty; at the tested penalty levels, a penalty-aware policy can outperform risk-neutral and nominal-exact objectives under correctly specified shared noise. **NEGATIVE TRANSFER OBSERVED:** the shared-model penalty-50 DP is inferior to nominal exact under independent shocks at penalty 50.

**NOT YET PROVEN:** real replay latency calibration, independent candidate-generator transfer, real evaluator utility, general scheduling superiority, security benefit, and production reliability. This is not an empirical benchmark of any live security system.

Next: freeze an **out-of-family candidate generator** (correlated costs/rewards, heavy-tailed costs) and **different latency distributions** (heavy-tailed, regime switches) before evaluating. Add an all-or-nothing completion reward and explicit dependent-reward controls. Only authorized, legitimate replay timing data could calibrate a real latency model. No main merge, deployment, paid CI rerun or external side effect.
