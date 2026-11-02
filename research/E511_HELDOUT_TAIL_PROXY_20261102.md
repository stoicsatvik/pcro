# E511 | Held-out 24-task completion-tail proxy falsification

Date: 2026-11-02. Continuation of E507–E510 on draft PCRO PR #25. **Synthetic-only; no measured replay latency or security evaluator.**

## Frozen hypothesis, before inspecting the E511 cohort

E510 proves an exact policy-ranking reversal under identical bivariate latency laws. E511 asks a narrower empirical question: **does the sign of a policy's complete-prefix probability advantage correctly predict the sign of its expected utility advantage?** This is a deliberately simple, policy-aware diagnostic, not a trained model or a claim of sufficient statistics.

- Freeze the E507 24-task fixture, E507 policy implementations, 400-unit deadline, truncation penalty 50, and two policies: DP50 versus exact400.
- Freeze two latency dependence families, Gaussian copula and Bernoulli common-shock mixture, both with marginal U[0.7,1.3] and target Pearson q=0.55. The Bernoulli mixture is evaluated by weighted independent/shared endpoints, not an extra sampled coin flip.
- **New, held-out fixture seeds 1024–1055**, not E507's 896–1023. Use 128 deterministic draws per seed with random seed `0xE5110000 ^ fixture_seed`; common random normals across policies.
- Compute for each policy and family (a) average realized utility and (b) probability the entire selected prefix finishes by 400. Compare **DP50 minus exact400**.
- Proxy prediction: sign of completion-probability gap predicts sign of utility gap, with a tie counted as no directional prediction. Predeclared pass criterion: at least **24/32** seeds with nonzero matching signs in each family. This is a strict, intentionally crude threshold, not a statistical significance test.
- Report both successes and failures, including zero-gap cases and the per-family mean utility gap. No refitting, no reseeding after viewing results.

## Why this test can fail

The completion indicator ignores how much reward is earned before a miss and the size of the selected reward set. Thus even a correct estimate of **full-prefix completion** may rank policies incorrectly on utility. The experiment tests a specific proxy; it does not test all possible cumulative-prefix or tail-risk features. Moreover, completion and utility are computed on the same simulated draws, so this is **not** independent predictive validation or empirical transfer.

## Reproduction

```bash
python -m unittest discover -s research -p 'test_e511_heldout_tail_proxy.py' -v
python research/e511_heldout_tail_proxy.py > e511_heldout_results.json
```

The dedicated `.github/workflows/e511-tail-proxy.yml` runs the controls and emits the fixed cohort summary. This report was committed **before reading the full-cohort results**. Any failures, lint issues, or workflow errors must be retained and corrected transparently.

## Pending results and limits

Exact-head GitHub CI and full-cohort summary pending. No outreach, hidden data, policy optimization, merge or deployment. If this simple proxy fails, the next gate is a predeclared prefix-weighted statistic evaluated on a separate seed cohort, not post-hoc tuning to E511.
