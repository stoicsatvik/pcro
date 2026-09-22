# PCRO Foundry State

## Scope

PCRO is restricted to post-competition, authorized replay/evaluator security research and synthetic benign cases. It must not target real services or users, bypass access controls, or be used for live competition submission activity.

The historical `competition/submission-v1` branch and PR #1 are **SUPERSEDED for Foundry work** by this scope. They are preserved as history and are not a basis for autonomous submission or live-target work.

## Current frontier

- Public evaluator mirror and synthetic replay tooling exist on `main`.
- `foundry/postcomp-parity-hardening` normalizes missing synthetic error values to the empty string at the adapter boundary.
- Exact implementation head `a6886caafd477a1702ec79231b031e0786f87201` executed Actions run `35157904755`.
- The independent `jed-parity` job completed **SUCCESS**, including installation of PCRO plus the pinned public JED SDK source and execution of the randomized evaluator-parity step. The bounded adapter/parity repair is therefore **SUPPORTED** by exact-head execution.
- The prior full `test` job exposed 27 repository-wide Ruff violations before pytest/property execution. This was tooling debt, not evaluator-parity failure.
- Isolated cleanup branch `foundry/ruff-debt-part1` reduced the demonstrated lint set to five reviewed semantic findings, then corrected those findings without weakening Ruff configuration. The one-shot fixer verified `ruff check .` successfully before committing implementation head `074eb82e5a4741e6d8cfdfe30f26502bf073fe3d` and removed itself from the resulting tree.

## Evidence discipline

Parity claims require an executed deterministic/random-seed corpus against a pinned evaluator implementation. A successful import or submission-schema validation is not parity evidence. Preserve mismatching seeds and traces rather than tuning them away.

Lint cleanup must not weaken the configured rule set merely to obtain a green badge. Semantic changes remain subject to the full pytest/property/parity contract.

## Claim state

- Pinned-SDK randomized evaluator parity at `a6886caafd477a1702ec79231b031e0786f87201`: **SUPPORTED**.
- Ruff cleanliness for cleanup implementation head `074eb82e5a4741e6d8cfdfe30f26502bf073fe3d`: **SUPPORTED** by the branch-scoped exact-tree lint verification.
- Repository-wide pytest/property/parity cleanliness after the lint cleanup: **NOT YET PROVEN** pending the normal CI workflow on the continuation head.
- Any claim about live systems, third-party targets, competition performance, attack effectiveness, or access-control bypass: outside Foundry scope and **NOT YET PROVEN**.

## Next move

Run the normal CI contract on this continuation: Ruff + pytest + 500-seed properties + pinned-SDK parity. If green, promote repository-wide CI cleanliness to SUPPORTED. Do not add attack-search capability, competition submission features, live-target integrations, or access-control bypass logic.
