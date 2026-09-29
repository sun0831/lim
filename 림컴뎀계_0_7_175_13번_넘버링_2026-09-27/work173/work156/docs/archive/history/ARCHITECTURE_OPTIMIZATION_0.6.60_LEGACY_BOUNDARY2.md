# 0.6.60 Legacy Event Boundary — follow-up

## Completed

- Moved the six live event handlers formerly stored in `legacy_event_compat_v1.py` into `event_runtime_v1.py`.
- Updated `GimmickRegistry` production callback methods to import the production event runtime instead of the compatibility module.
- Reduced `legacy_event_compat_v1.py` to compatibility-only re-export wrappers.
- Added `test_v105_production_event_boundary.py` to prevent production code from importing the compatibility module.
- Verified the existing migration/fire-event boundary tests still pass.

## Verification

- Targeted boundary/integration tests: **15 passed**
- Full regression: **390 passed**
- Python compile: **PASS**
- Remaining `legacy_event_compat_v1` references: **tests only**

## Remaining Legacy work

Direct `TriggerRuntime` references remain in two categories:

1. **Explicit compatibility/parity**
   - `special_gimmick_v2.py` lazy `trigger_runtime` property and `fire_event_compat()`
   - `golden_rule_parity_v1.py`
   - migration/parity documentation and tests

2. **Probabilistic branch runtime inside `one_turn_solver_v29.py`**
   - branch-local trigger evaluation still instantiates `TriggerRuntime` for deferred/probabilistic rules.
   - This must be migrated separately; it is not safe to remove as part of the event-boundary change.

The next Legacy task is therefore the probabilistic branch migration, followed by a production-path dependency audit and only then retirement of dead compatibility code.
