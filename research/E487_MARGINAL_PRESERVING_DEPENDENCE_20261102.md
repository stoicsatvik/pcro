# E487 | Fixed-marginal latency-dependence falsification

Date: 2026-11-02. Scope: **offline synthetic scheduling**, not live replay, exploitation, or evaluator access.

## Question and predeclared design

E473's interpolated shock family altered marginal variance, confounding dependence with dispersion. E487 fixes every individual latency factor to U[0.7,1.3) while varying dependence: with probability q, all 24 factors share one uniform draw; otherwise they are independent uniforms. Pairwise Pearson correlation equals q exactly in this model. The full joint distribution varies, so no universal causal interpretation of q is justified.

Frozen E455/E473 policies: exact400, exact360, expected-prefix DP penalty50 and penalty100, chance90. New fixture seeds 768–895 (128 independent synthetic fixtures), 128 paired deterministic draws per fixture, budget 400, completed-prefix utility minus 50 for truncation. No fitting or policy tuning on this cohort.

## Exact paired Monte Carlo results (difference from exact400)

| Policy | q=0 independent | q=0.25 | q=0.5 | q=0.75 | q=1 shared |
| --- | ---: | ---: | ---: | ---: | ---: |
| exact360 | +2.528 | -0.319 | -3.167 | -6.014 | -8.862 |
| dp50 | **-19.270** | -12.140 | -5.010 | +2.121 | **+9.251** |
| dp100 | +0.643 | +0.441 | +0.238 | +0.036 | -0.166 |
| chance90 | -35.753 | -32.342 | -28.930 | -25.519 | -22.108 |

DP50 descriptive 95% seed-standard-error intervals: independent [-21.752,-16.788], shared [+8.026,+10.476]. The model-specific zero crossing is q*=0.675649 by the exact affine expectation identity E_q[U]=(1-q)E_ind[U]+q E_shared[U]. These intervals are descriptive for deterministic synthetic fixtures, not calibrated empirical population confidence.

## Reproducibility and independent checks

Run `node research/e487_marginal_preserving_copula.mjs` on Node 22. This source includes nine exhaustive 8-option DP oracle checks (three seeds x three penalties), survival boundaries, shared-vector assertions, a two-job analytical check (probability both fit: independent 1/18, shared 1/6, half-mixture 1/9), and exact affine-mixture assertions. Native Node 22 execution on the locally byte-identical file passed on 2026-11-02; an independent Python check of the mixture and crossover passed. GitHub source blob SHA-1 `184cff119f231ca16200d4fc95d60407cdc472ad` equals the locally executed file's Git blob SHA.

**SUPPORTED IN THIS SYNTHETIC MODEL:** DP50 changes sign as dependence varies while every one-dimensional latency marginal remains unchanged. **REJECTED:** E473's endpoint sign reversal requires a change in marginal variance. **NOT YET PROVEN:** robustness to other copulas at matched correlation, real-world latency correlation, actual evaluator utility, minimax regret or CVaR superiority.

Next: independently test Gaussian/rank copulas and adversarial dependence at fixed marginals, then evaluate minimax regret and tail risk on fresh seeds. No empirical latency data are claimed. No main merge, deployment, spending, competition submission, or third-party interaction.
