# 0.6.50 — support_action → SupportActionResolver → ActionQueue migration

## Goal
Migrate catalog `support_action` TriggerRule effects into the common Rule IR / EffectExecutor boundary while preserving the existing SupportActionResolver semantics.

## Changes
- `EffectRuntime.GENERIC_EXECUTABLE_EFFECTS` now includes `support_action`.
- `EffectExecutor` adds `_support_action()`.
- Formation-relative identity selection delegates to `SupportActionResolver`.
- `requested_next` / `__support_default__` keeps the existing solver-level placeholder semantics.
- Named/first-attack support skills resolve through the common resolver before queue insertion.
- Generated actions are inserted through `ActionQueue.triggered_from()` and preserve trigger kind, target policy, target IDs, coin targets, source attribution, and depth.
- Missing queue/source or unresolved support identity/skill returns deferred without consuming activation.
- Legacy `special_gimmick_v2` support-action branch is skipped when migration execution succeeds, preserving Legacy compatibility for non-migrated cases.

## Migration result
- TriggerRule total: 55
- migration-safe: 38
- deferred: 17
- unknown: 0
- `support_action`: 6 rules migrated to generic-safe execution.

## Tests
- Support-focused tests: 6 passed
- Full regression: 363 passed
- Python syntax compilation: PASS

## Notes
The six newly safe rules are not treated as ordinary `queue_action`: their identity/skill selection remains delegated to `SupportActionResolver`, and `requested_next` deliberately remains a solver placeholder so the user's requested action order semantics are preserved.
