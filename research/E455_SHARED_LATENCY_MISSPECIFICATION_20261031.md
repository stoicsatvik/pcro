# E455 | Shared-latency misspecification and truncation penalties (31 October 2026)

**Status:** isolated, dependency-free synthetic research; draft/unmerged. No real timing traces, evaluator interaction, deployment or outreach.

## Falsifiable question

E454's exact expected-prefix DP optimizes cumulative reward under one assumed common latency multiplier `U ~ Uniform[0.7,1.3)`, but its schedules truncate about 95% of the time. Does the advantage survive (a) an explicit penalty for incomplete schedules and (b) a misspecified shared-latency distribution?

Fix a **realized utility** before evaluation:
`V = E[prefix reward] - 100 * P(schedule truncates)`.
All policies are selected without looking at the evaluation distribution. The 100-unit penalty is a synthetic sensitivity choice, **not** a measured evaluator penalty.

## Frozen design

- E454 nominal 400-ms knapsack and density-ordered shared-prefix DP are reproduced with the same LCG fixture definition. The latter is extended with a terminal expected-truncation penalty of `lambda = 0, 25, 100, 500` while optimizing under the **same assumed** `U[0.7,1.3)`.
- Evaluate each fixed policy analytically under three **fully shared** multiplier families: assumed `U[0.7,1.3)`, slower `U[0.9,1.5)`, faster `U[0.5,1.1)`. Exact survival for cumulative nominal cost C is `clip((400/C-low)/(high-low),0,1)`.
- Two deterministic seed populations: LCG seeds 384–511 (128 new seeds from the E454 family), and independent xorshift-generated costs/rewards seeds 1000–1127 (128 from a different generator and range). Each seed has 24 abstract options. **Seeds within a generator are not independent field measurements.**
- `risk0` is the original expected-prefix objective; `risk100` optimizes exactly the evaluation penalty under the assumed family; `risk500` is a more completion-conservative sensitivity.

## Executed controls

The unchanged standalone Node 22 script `research/e455_latency_misspecification.mjs` ran locally with **24/24 assertions**:
- 16 exhaustive 8-option, density-ordered subsequence controls across four penalties and four seeds;
- two survival-probability boundary checks;
- four zero-penalty identity checks;
- two independent exact analytic E454 holdout controls, reproducing the reported means **630.789093** (nominal exact) and **658.110632** (shared DP) on E454 seeds 256–383.

The GitHub-committed script's blob SHA is `095b7fd37854be28261e474398b187ceb57a26f4`, equal to the locally executed script. No external packages, Monte Carlo draws or GitHub Actions were required.

## Results: mean utility with evaluation truncation penalty 100

| Population | Evaluation multiplier | Nominal exact 400 | risk0 | risk25 | risk100 | risk500 |
|---|---|---:|---:|---:|---:|---:|
| LCG 384–511 | assumed 0.7–1.3 | 577.918 | 557.488 | 567.825 | **584.856** | 572.330 |
| LCG 384–511 | slower 0.9–1.5 | 495.229 | 478.481 | 478.675 | 508.775 | **520.769** |
| LCG 384–511 | faster 0.5–1.1 | 642.334 | 662.989 | **663.634** | 633.481 | 573.133 |
| Xorshift 1000–1127 | assumed 0.7–1.3 | 557.085 | 535.060 | 547.774 | **566.749** | 554.701 |
| Xorshift 1000–1127 | slower 0.9–1.5 | 478.436 | 461.820 | 462.132 | 497.729 | **506.592** |
| Xorshift 1000–1127 | faster 0.5–1.1 | 620.202 | 634.714 | **637.354** | 606.083 | 555.297 |

**Preserved negative results:** under the assumed multiplier and 100-unit truncation penalty, unpenalized `risk0` loses to nominal exact by **20.430** (LCG) and **22.025** (xorshift). Under the slower family, `risk0` has **zero completion probability** in both populations. Under the faster family, overconservative `risk500` loses to nominal exact by **69.201** (LCG) and **64.905** (xorshift).

Under the assumed family, `risk100` completion probability is **0.6692** (LCG) and **0.7369** (xorshift), versus `risk0` **0.0524** and **0.0514**. The penalty changes the schedule rather than merely changing how a fixed schedule is scored.

## Interpretation and constraints

The E454 unpenalized DP is **not robustly superior** once incomplete schedules carry a penalty. The optimal penalty-sensitive policy changes with the unknown latency family; no single fixed penalty setting wins all three families in either generator population. These are deterministic **analytic expectations under chosen uniform distributions**, not empirical latency measurements, confidence intervals or proof of general scheduler superiority.

The DP is exact only over subsequences of a frozen **density order**, not all permutations. The xorshift population changes the fixture generator and cost/reward ranges, but remains synthetic. All evaluation distributions are fully shared and uniform; the experiment does not establish behavior under correlated-but-not-identical latencies, heavy tails, deadline changes, score-cell dependence or nonadditive rewards. There is no validated real-world truncation penalty of 100.

## Next gate

Measure authorized real timing traces and completion penalties; freeze an out-of-family validation distribution; compare a robust/chance-constrained policy against the nominal, unpenalized and penalty-aware DPs, including all-or-nothing scoring. Do **not** promote any policy or claim real evaluator gains from this synthetic result. Keep stacked on E454 draft PR #19, without merge/deployment.
