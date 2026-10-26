# E287 | Complete exact k-wise independence tail-identifiability frontier

**Date:** 2026-10-26. **Scope:** abstract exchangeable eight-outcome probability model. No replay data, attack execution, hidden evaluation, or empirical risk claim.

## Decisive question

E260 and E276 showed that pairwise and triplewise independence do not identify the eight-way all-failure probability. **How much higher-order independence would be required to identify it?** Rather than another isolated k, E287 exhausts all k from 1 through 8.

Let K be the number of successes among eight exchangeable binary outcomes, each marginally successful with probability 1/2. For k-wise independence, the first k factorial moments are fixed: E[(K)_j] = (8)_j / 2^j for j = 0,...,k.

For each k, enumerate all combinations of k+1 support points from K in {0,...,8}; solve the full-rank moment system with exact Fraction Gaussian elimination; reject negative masses. Every vertex of the bounded moment polytope has at most k+1 support points, so this finite enumeration is exhaustive for extrema of P(K=0). Independently verify every j-bit pattern, j<=k, from the exchangeable joint law.

## Sharp mathematical bounds

| k-wise independence | Sharp min P(all fail) | Sharp max P(all fail) | Max / full independence |
|---:|---:|---:|---:|
| 1 | 0 | 1/2 | 128× |
| 2 | 0 | 1/10 | 25.6× |
| 3 | 0 | 1/16 | 16× |
| 4 | 0 | **1/40 (2.5%)** | **6.4×** |
| 5 | 0 | 1/72 | 3.5556× |
| 6 | 0 | 1/112 | 2.2857× |
| 7 | 0 | **1/128** | **2×** |
| 8 | **1/256** | **1/256** | **1×** |

Every bound is attained by an explicit exact exchangeable count law emitted by `experiments/e287_kwise_tail_identifiability_frontier.py`. The number of feasible full-rank bases for k=1,...,8 is respectively 24, 31, 35, 25, 25, 18, 9, 1. All values are exact, not floating-point LP estimates.

**Negative result:** Even complete 7-wise independence can leave the eight-way all-failure probability anywhere between 0 and 1/128. Full eight-way independence is necessary to identify the tail *under these frozen assumptions*. Four-way independence reduces the worst case to 1/40, but that is still 6.4× the full-independence value.

## Claims and limits

- **PROVEN FOR THE SPECIFIED ABSTRACT MODEL:** exact k-wise identifiability frontier and sharp extrema for n=8, p=1/2, exchangeable laws.
- **NOT YET MEASURED:** empirical joint replay-family outcomes or actual catastrophic-failure frequency.
- **NOT PROVEN:** real candidate independence, cross-family dependence, robustness against hidden evaluators.
- The exchangeability and marginal assumptions are stipulated, not inferred from real systems.

**Next highest-EV experiment:** stop extending synthetic k-wise ladders. Obtain legitimate authorized joint replay vectors with run IDs preserved, estimate held-out co-failure with uncertainty, and test whether a shared-shock latent model explains the observed dependence. No invented replay observations.

**Validation:** `pytest tests/test_e287_kwise_tail_identifiability_frontier.py`, full PCRO CI, and machine-readable exact-rational receipt. No main merge.
