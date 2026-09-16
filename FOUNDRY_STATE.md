# PCRO Foundry State

## Scope

PCRO is restricted to post-competition, authorized replay/evaluator security research and synthetic benign cases. It must not target real services or users, bypass access controls, or be used for live competition submission activity.

The historical `competition/submission-v1` branch and PR #1 are **SUPERSEDED for Foundry work** by this scope. They are preserved as history and are not a basis for autonomous submission or live-target work.

## Current frontier

- Public evaluator mirror and synthetic replay tooling exist on `main`.
- The pinned public SDK parity workflow previously crashed before producing a parity verdict because synthetic events without errors were lowered as `None`, while the SDK cell-signature implementation expects a string and calls `startswith` on the field.
- `foundry/postcomp-parity-hardening` normalizes missing synthetic error values to the empty string at the adapter boundary.
- This repair is **NOT YET PROVEN** until exact-head CI executes the randomized parity harness successfully.
- A historical PR workflow also has repository-wide Ruff debt. Lint failures must not be confused with evaluator-parity failures.

## Evidence discipline

Parity claims require an executed deterministic/random-seed corpus against a pinned evaluator implementation. A successful import or submission-schema validation is not parity evidence. Preserve mismatching seeds and traces rather than tuning them away.

## Next move

Run the pinned-SDK parity harness on the exact branch head. If it reaches semantic mismatches, preserve the first mismatch corpus and fix only demonstrated contract differences. Do not add attack-search capability or competition submission features.
