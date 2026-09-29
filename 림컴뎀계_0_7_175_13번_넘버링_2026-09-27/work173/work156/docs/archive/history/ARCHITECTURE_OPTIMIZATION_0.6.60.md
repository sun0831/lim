# Architecture Optimization 0.6.60 — Legacy Event Boundary Completion

## Scope

This release continues item 1: separating the retired `TriggerRuntime` from the production event path.

## Changes

- `GimmickRegistry.fire_event()` now routes through `_fire_migrated_event()` / `RuleMigrationRuntime.production_fire()`.
- Added `GimmickRegistry.fire_event_compat()` as the explicit compatibility-only entrypoint for the old `TriggerRuntime`.
- Existing lazy `trigger_runtime` access remains compatibility-only.
- Added `test_v104_fire_event_boundary.py` to prove:
  - production `fire_event()` does not call `TriggerRuntime.fire()`;
  - the only direct legacy event API is explicitly named as compatibility;
  - the migration boundary reports deferred execution rather than silently falling back.

## Verification

- Boundary tests: 9 passed.
- Full regression: 387 passed.
- Python compile: to be run with release packaging.

## Remaining item 1 work

1. Audit every remaining direct `TriggerRuntime` reference and classify it as production, compatibility, or probabilistic branch runtime.
2. Prove that no live combat path depends on the compatibility runtime.
3. Remove only production-dead compatibility branches after boundary tests exist.
4. Re-run full regression and golden tests.

## Progress

Item 1 (`Legacy ↔ Generic separation`) is estimated at **~82%**, up from ~78% in 0.6.59. This is a structural estimate, not a game-mechanics completeness percentage.
