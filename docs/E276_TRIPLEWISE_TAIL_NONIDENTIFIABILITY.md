# E276 | Triplewise independence still does not identify catastrophic tails

**Date:** 2026-10-26. **Scope:** exact abstract exchangeable Bernoulli mathematics, not measured agent replay performance.

## Decisive question

E260 proved that eight equal-marginal outcomes can have zero pairwise covariance yet catastrophic all-fail risk between 0 and 10%. Does measuring all triplewise joint probabilities eliminate the ambiguity?

**No.** Even when **every one of the 56 triples is fully independent** (all eight patterns per triple have probability exactly 1/8), the probability that all eight candidates fail can still vary from **0% to 6.25%**. Fully independent outcomes predict only **1/256 = 0.390625%**. The sharp worst case is **16 times** the independent prediction.

Let K be the number of successes among eight exchangeable binary outcomes. Conditional on K=k, choose a uniformly random k-subset of successful candidates. All three laws below satisfy exactly:

- E[K] = 4
- E[K(K−1)] = 14
- E[K(K−1)(K−2)] = 42

These factorial moments imply every individual, pair and triple has the same joint probabilities as independent fair Bernoulli variables.

| Law | Exact distribution of K | P(all fail) |
|---|---|---:|
| Zero-tail | P(K=1)=1/15; P(K=3)=1/3; P(K=4)=1/3; P(K=6)=4/15 | **0** |
| Independent | P(K=k)=C(8,k)/256 | **1/256** |
| Maximum-tail | P(K=0)=1/16; P(K=4)=7/8; P(K=8)=1/16 | **1/16** |

## Sharp bound certificate

For every integer k from 0 through 8:

\[
\mathbf{1}[k=0] \leq \frac{(k-4)^2(8-k)}{128}.
\]

The right side is nonnegative for every allowed k, equals one at k=0, and vanishes at k=4 and k=8. Using the frozen factorial moments gives E[K²]=18 and E[K³]=88, hence

\[
P(K=0) \leq \frac{-88+16(18)-80(4)+128}{128}=\frac{1}{16}.
\]

The maximum-tail law attains this upper bound; the zero-tail law attains the trivial lower bound zero. An **independent exact-Fraction enumeration** solves all C(9,4)=126 four-support moment systems, finding 35 feasible vertices and the same sharp extrema. The tests explicitly enumerate all 256 outcomes and verify every one of the 56 triples' eight binary patterns for all three laws.

**Falsified inference:** even perfect empirical knowledge of one-, two- and three-way independence is not sufficient to infer eight-way joint independence or a calibrated catastrophic-risk forecast.

**SUPPORTED (exact mathematics):** 0–1/16 all-fail bound for this frozen eight-candidate exchangeable model with the first three independent-Bernoulli factorial moments.

**NOT YET PROVEN:** any such law describes observed agent replays, and no empirical all-fail frequency was measured.

**Reproduce:** `python experiments/e276_triplewise_tail_nonidentifiability.py` and `pytest tests/test_e276_triplewise_tail_nonidentifiability.py`. CI uploads an exact JSON certificate. No exploit traces, hidden evaluators, unauthorized testing or external targets.

**Next measurement:** collect legitimate, jointly identified eight-candidate replay outcomes with preserved run IDs. Compare observed co-failure moments and held-out all-fail counts against the independence forecast and moment-compatible bounds. If tail events are too rare, report honest uncertainty rather than promoting an assumed copula into a measured risk estimate.
