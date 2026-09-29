# Architecture Optimization 0.6.59 — Legacy separation continuation

## Goal
Continue item 1: separate old/compatibility execution from the production Generic Rule Runtime.

## Changes
- Moved `after_skill` compatibility handler out of `special_gimmick_v2.py` into `legacy_event_compat_v1.py`.
- Made `GimmickRegistry.trigger_runtime` lazy: production construction no longer instantiates `TriggerRuntime`.
- `reset_turn()` only resets the legacy runtime when compatibility code has actually requested it.
- Added explicit boundary regression coverage for lazy legacy runtime creation.
- Preserved public compatibility APIs and existing test behavior.

## Result
- `special_gimmick_v2.py`: 811 → 662 lines in this cycle.
- `legacy_event_compat_v1.py`: 459 → 613 lines.
- Production Rule dispatch remains through `RuleMigrationRuntime.production_fire()`.
- Legacy TriggerRuntime is now an explicit compatibility object rather than a production-created runtime.

## Verification
- Full regression: 385 passed.
- Python compile: PASS.

## Item 1 progress
Estimated completion: ~78%.

Remaining for item 1:
1. isolate `fire_event()` as an explicit compatibility API;
2. audit remaining direct `TriggerRuntime`/manual-effect paths;
3. remove only proven production-dead compatibility branches;
4. add boundary tests for each removed path;
5. confirm production has zero Legacy execution dependencies.

This percentage is a structural estimate, not a game-mechanics completeness percentage.
