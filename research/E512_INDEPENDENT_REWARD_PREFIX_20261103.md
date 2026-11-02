# E512 | Independent-draw reward-weighted prefix diagnostic

Date: 2026-11-03. Continuation of E511 on draft PR #25. **Preregistered before evaluating this cohort.**

## Frozen question and rejection rule

E511's full-prefix completion-only sign proxy failed its 75% gate in the Gaussian family (16/32) despite a Bernoulli-family pass (25/32). Does a reward-weighted *completed-prefix* score better predict the sign of DP50 minus exact400 expected utility when the diagnostic and evaluation draws are independent?

- Freeze E507's 24-task fixtures, policy selection, budget 400, penalty 50, Gaussian copula and Bernoulli independent/shared mixture at q=0.55. Do not refit or change policies.
- Use **fresh fixture seeds 1056–1087** (32), disjoint from E507 and E511. For each seed draw **128 independent diagnostic scenarios** and **128 independent outcome scenarios**, with separate deterministic RNG streams `0xE512A000 ^ seed` and `0xE512B000 ^ seed`. Reuse paired random variates across policies, but never between diagnostic and outcome streams.
- Define `S(policy) = sum_k reward_k * P(sum_{j<=k} nominal_cost_j * factor_j <= 400)`, estimated using diagnostic scenarios. The **prefix score excludes the missed-task penalty**. Define the E511 baseline as probability that the *entire* policy finishes within 400, estimated on the same diagnostic scenarios.
- For each policy and family, estimate actual expected utility independently from outcome scenarios using frozen `realized()`. Predict the sign of the DP50-minus-exact400 utility gap using either diagnostic score difference. Ties count as failures to make a directional prediction.
- **Pass gate**: reward-prefix sign agreement at least **24/32 in both families**, and strictly more agreements than the completion-only baseline in **each** family. Report failures, per-family sign disagreements, ties, mean utility gaps and mean score gaps. No post-hoc threshold changes, new seeds or tuning.

## Interpretation limits

This is synthetic scheduling, not observed runtime. The completed-prefix reward on a *single draw* equals `realized + 50` if the selected policy misses a task, and `realized` otherwise. Thus the score is closely tied to utility by construction; it is **not a causal explanation** of dependence-family ranking and excludes the failure penalty. Independent diagnostic and outcome draws prevent direct same-sample reuse, but not shared synthetic data-generating assumptions. A positive result cannot validate real-world performance. A negative result falsifies this frozen proxy/gate only.

## Reproduction

```bash
python -m unittest discover -s research -p 'test_e512_reward_prefix_proxy.py' -v
python research/e512_reward_prefix_proxy.py
```

The full 32-seed result must be appended below only after the frozen implementation and tests are committed. Keep any failed CI or contradictory results visible.

## Results (pending preregistered evaluation)


## Observed frozen-cohort results (no refitting)

[Exact-head E512 workflow #41506853453](https://github.com/stoicsatvik/pcro/actions/runs/41506853453) succeeded with **7/7 deterministic controls** and the preregistered 32-seed experiment. Each seed had 128 independent diagnostic and 128 independent outcome draws, with the two copula families evaluated using the frozen q=0.55 laws.

| Family | Mean independent outcome utility gap (DP50 - exact400) | Mean reward-prefix score gap | Reward-prefix matching signs | Completion-only matching signs | Reward-prefix opposing signs | Predeclared gate |
|---|---:|---:|---:|---:|---:|---|
| Gaussian | **-0.438477** | +12.326660 | **15/32** | 13/32 | 13 | **FAIL** |
| Bernoulli mixture | **-6.007361** | +9.842224 | **4/32** | 24/32 | 24 | **FAIL** |

Both families had four reward-prefix proxy ties and four independent outcome utility ties. The Gaussian reward-prefix diagnostic improves over the completion-only baseline by two matching seeds, but remains far below the 24/32 gate. **The Bernoulli reward-prefix diagnostic is much worse than the completion-only baseline (4/32 versus 24/32).** Neither family passes the frozen joint gate.

**Negative finding retained:** The diagnostic predicts a positive *average* reward-prefix gap in both families, while the independent outcome estimates show negative *average* utility gaps. A score that omits the 50-unit missed-task penalty can systematically favor a policy that earns more partial-prefix reward but suffers greater failure costs. This is consistent with the reward/penalty accounting identity, but the experiment does not identify a unique causal mechanism. Four ties further limit directional coverage.

The experiment cannot establish statistical generalization beyond these deterministic synthetic cohorts; there are no uncertainty intervals, measured replay latencies, external validity claims, or fitted coefficients. Do **not** repair the failed gate by changing the threshold, seeds or feature after inspection. A penalty-aware full-prefix score could reproduce the existing utility definition algebraically and would be a poor independent scientific test; a more valuable next step is to obtain real latency traces, validate dependence models and test a genuinely reduced-order predictor under a frozen train/holdout split.
