# E509 | Pairwise-identical latency models can disagree on three-task completion

Date: 2026-11-02. Continuation of E507/E508, draft PCRO PR #25. All results below are exact synthetic calculations, not observed replay latency.

## Falsifiable question

Does matching **all pairwise joint distributions** of three latency multipliers, not merely their marginals and Pearson correlations, guarantee the same probability of completing a three-task prefix under a deadline? **No.**

Take two independent fair bits A and B. In the even-parity model, let C=A XOR B; in the odd-parity model, C=1 XOR A XOR B. The four bit triples in each model are equiprobable. Every individual bit is fair, and every bit pair is independent and uniform over (00,01,10,11), in **both** models.

Independently draw three U[0,1) jitters U_i. Convert each bit b_i to a continuous latency factor F_i = 0.7 + 0.3(b_i+U_i). Thus **each F_i is exactly U[0.7,1.3)** and every **pair** (F_i,F_j) is a product of two independent U[0.7,1.3) distributions in either model. All pairwise Pearson correlations are exactly zero; all pairwise joint tail probabilities match at every threshold, not just at 1.0.

But P(F1>1,F2>1,F3>1) is **0** for even parity and **1/4** for odd parity. The independent three-factor baseline gives **1/8**.

## Exact deadline counterexample

Three tasks each have 100 ms nominal latency. The deadline is 300 ms. The full prefix completes exactly when F1+F2+F3 <= 3. Write K as the number of high bits and S as the sum of three independent U[0,1) jitters. Then F1+F2+F3 = 2.1 + 0.3(K+S). Deadline overrun occurs when S>3-K. The exact Irwin-Hall(3) tails for K=0,1,2,3 are respectively 0, 1/6, 5/6, 1.

| Model | K support and probabilities | P(overrun) | P(complete) |
|---|---|---:|---:|
| Even parity | K=0 (1/4), K=2 (3/4) | 5/8 | **3/8** |
| Independent | K~Binomial(3,1/2) | 1/2 | **1/2** |
| Odd parity | K=1 (3/4), K=3 (1/4) | 3/8 | **5/8** |

The two pairwise-indistinguishable models therefore differ by **25 percentage points** in full-prefix completion probability. This is an exact mathematical counterexample, not a fitted or sampled effect.

## Validation and limits

`research/test_e509_parity_copula.py` exhaustively checks both four-state bit laws, all three pairwise tables, triple-tail disagreement, and exact fractional deadline probabilities, including the independent baseline. Run with `python -m unittest discover -s research -p 'test_e509_parity_copula.py' -v`.

- The construction has **zero pairwise correlation**; it does not directly reproduce E507's q=0.55 sign reversal.
- Three nominally equal tasks are an analytic counterexample, not the frozen E507 24-task fixture or its policy comparison.
- The result falsifies any guarantee based only on pairwise latency diagnostics. It does **not** identify which dependence model occurs in production or prove a particular scheduler superior.
- Next gate: predeclare an interpretable cumulative-prefix tail statistic and test its out-of-sample predictive value for the *frozen* E507 policies across fresh copula families and seeds. Do not infer generalization from this constructed example.

No external data, private evaluator access, outreach, production code, merge or deployment.
