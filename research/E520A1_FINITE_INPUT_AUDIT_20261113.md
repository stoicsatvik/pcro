# E520A1 — finite-input and CSV schema hardening

Date: 13 November 2026  
Branch: `research/e520-cross-environment-order-replication-20261113`  
Parent experiment: E520A task-rank stability reconciliation

## Defect identified

The E520A rank audit converted `duration_ms` to float and checked only `value <= 0`. IEEE-754 NaN does not satisfy that comparison, and infinities are positive. A malformed or partially corrupted CSV could therefore reach the rank calculation and produce undefined ordering or a misleading result.

The original `csv.DictReader` path also did not reject duplicate column names. Python's dictionary mapping can overwrite one duplicate value silently. The audit did not explicitly reject missing required headers, empty run IDs, or unheaded extra row fields.

## Changes

- Require unique, non-empty CSV headers and the exact required fields `run_id`, `task_id`, and `duration_ms`.
- Reject extra row fields, empty required values, and empty run IDs.
- Parse task IDs and durations once, then require finite, strictly positive durations before any rank calculation.
- Make the Spearman helper independently reject non-finite inputs.

## Falsifiable regression cases

Added `tests/test_e520_task_rank_stability_audit.py` covering:
- NaN, +infinity and -infinity duration values;
- duplicate headers;
- missing required headers;
- an unheaded extra row field;
- non-finite direct Spearman inputs;
- unchanged finite perfect-rank behavior.

## Result boundary

This is input-integrity hardening only. It does not change the E520 primary slope, permutation result, rank estimand, or scientific interpretation. No new observations were collected and no E520 result is recomputed in this addendum.

The repository Actions allowance is exhausted, so exact-head GitHub CI cannot currently validate the new commit. The regression suite must be run locally or after runner capacity returns. Until then, the new tests are committed but **not claimed as executed**.
