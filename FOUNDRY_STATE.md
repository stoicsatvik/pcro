# PCRO Foundry State

## Scope

PCRO is restricted to post-competition, authorized replay/evaluator security research and synthetic benign cases. It must not target real services or users, bypass access controls, or be used for live competition submission activity.

The historical `competition/submission-v1` branch and PR #1 are **SUPERSEDED for Foundry work** by this scope. They are preserved as history and are not a basis for autonomous submission or live-target work.

## Current frontier

- Public evaluator mirror and synthetic replay tooling exist on `main`.
- `foundry/postcomp-parity-hardening` normalizes missing synthetic error values to the empty string at the adapter boundary.
- Exact implementation head `a6886caafd477a1702ec79231b031e0786f87201` executed Actions run `35157904755`.
- The independent `jed-parity` job completed **SUCCESS**, including installation of PCRO plus the pinned public JED SDK source and execution of the randomized evaluator-parity step. The bounded adapter/parity repair is therefore **SUPPORTED** by exact-head execution.
- The latest full `test` job exposed 27 repository-wide Ruff violations before pytest/property execution. This is tooling debt, not evaluator-parity failure.
- `foundry/ruff-debt-part1` is an isolated cleanup continuation. It contains a one-shot branch-scoped workflow that applies only Ruff's safe deterministic fixes; the bot-authored follow-up is prevented from recursively rerunning the fixer.

## Evidence discipline

Parity claims require an executed deterministic/random-seed corpus against a pinned evaluator implementation. A successful import or submission-schema validation is not parity evidence. Preserve mismatching seeds and traces rather than tuning them away.

Lint cleanup must not weaken the configured rule set merely to obtain a green badge. Safe mechanical fixes may be automated on the isolated branch; semantic violations must be reviewed and corrected explicitly.

## Claim state

- Pinned-SDK randomized evaluator parity at `a6886caafd477a1702ec79231b031e0786f87201`: **SUPPORTED**.
- Repository-wide CI/test cleanliness: **NOT YET PROVEN** because Ruff currently prevents pytest/property execution in the `test` job.
- Any claim about live systems, third-party targets, competition performance, attack effectiveness, or access-control bypass: outside Foundry scope and **NOT YET PROVEN**.

## Next move

Execute the branch-scoped safe Ruff cleanup, inspect the remaining semantic violations, correct them without changing evaluator behavior, then rerun Ruff + pytest + 500-seed properties + pinned-SDK parity. Do not add attack-search capability, competition submission features, live-target integrations, or access-control bypass logic.
