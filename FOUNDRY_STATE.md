# PCRO Foundry State

## Scope

PCRO is restricted to post-competition, authorized replay/evaluator security research and synthetic benign cases. It must not target real services or users, bypass access controls, or be used for live competition submission activity.

The historical `competition/submission-v1` branch and PR #1 are **SUPERSEDED for Foundry work** by this scope. They are preserved as history and are not a basis for autonomous submission or live-target work.

## Current frontier

- Public evaluator mirror and synthetic replay tooling exist on `main`.
- `foundry/postcomp-parity-hardening` normalizes missing synthetic error values to the empty string at the adapter boundary.
- Exact implementation head `a6886caafd477a1702ec79231b031e0786f87201` executed Actions run `35157904755`.
- The independent `jed-parity` job completed **SUCCESS**, including installation of PCRO plus the pinned public JED SDK source and execution of the randomized evaluator-parity step. The bounded adapter/parity repair is therefore **SUPPORTED** by exact-head execution.
- The overall workflow remains red because the separate `test` job stopped at repository-wide `ruff check .`; pytest and property checks in that job were skipped. This lint debt must not be misreported as a parity failure, and it also means the repository-wide test contract is not yet green.

## Evidence discipline

Parity claims require an executed deterministic/random-seed corpus against a pinned evaluator implementation. A successful import or submission-schema validation is not parity evidence. Preserve mismatching seeds and traces rather than tuning them away.

## Claim state

- Pinned-SDK randomized evaluator parity at `a6886caafd477a1702ec79231b031e0786f87201`: **SUPPORTED**.
- Repository-wide CI/test cleanliness: **NOT YET PROVEN** because Ruff failed before pytest/property execution in the `test` job.
- Any claim about live systems, third-party targets, competition performance, attack effectiveness, or access-control bypass: outside Foundry scope and **NOT YET PROVEN**.

## Next move

Fix only the demonstrated repository-wide Ruff debt on an isolated continuation of this branch, then rerun the full test/property contract. Do not add attack-search capability, competition submission features, live-target integrations, or access-control bypass logic.
