# B/C Implementation Report — 2026-09-21

## B — SPEC

Added `RULEIR_EXECUTION_BOUNDARY_SPEC_0.7.0.md`.

The SPEC fixes the distinction between:

- definition (`RuleIR` / `TriggerRule`)
- mutable activation state (`ActivationLedger`)
- common execution (`RuleRuntime`)
- production migration boundary (`RuleMigrationRuntime.production_fire`)
- temporary parallel audit (Legacy vs RuleIR on isolated state)
- actual-game Golden validation

It explicitly states that RuleIR conversion coverage is not gameplay execution coverage.

## C — RuleIR execution boundary

The project already had the production boundary implemented through:

`RuleMigrationRuntime.production_fire()`

and the catalog production path in `special_gimmick_v2._fire_migrated_event()`.

This pass adds 5 focused tests in `test_rule_ir_execution_boundary_c.py` to freeze that boundary:

1. migration-safe production rules do not enter `TriggerRuntime`
2. deferred rules fail fast at the production boundary
3. temporary parallel audit compares Legacy and RuleIR results
4. parallel audit uses independent rule copies and does not mutate the definition
5. live `RuleRuntime` owns activation through `ActivationLedger`

No new execution Runtime family was introduced.

## Validation

Fast:

`python run_tests.py --fast`

**659 passed, 9 deselected in 3.07s**

Slow:

`python -m pytest -q -m slow`

**9 passed, 659 deselected in 31.27s**

Combined partitioned suite: **668 passed**.

## Boundary status

C is now explicitly frozen as an execution-boundary contract, but this does NOT mean all 360 RuleIR gap records are executable.

The next implementation step is D: connect migration-safe RuleIR execution to the damage/action execution path and establish the first real damage Golden cases.
