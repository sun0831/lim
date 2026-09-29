# Engine Conversion Audit — 0.7.0

## Scope
This audit covers the current `identity_catalog_v2.json` trigger-rule compilation boundary. It does not claim that all identity skill/passive effects are implemented.

## Result
- Identity catalog input: 184 identities
- Compiled trigger rules: 55
- Common Runtime safe: **55 / 55 (100%)**
- Deferred trigger rules: **0**
- Unknown trigger rules: **0**
- Production direct `TriggerRuntime` construction/import in the `_fire_migrated_event` path: **0**

## Interpretation
The trigger-rule layer has crossed the Common Rule IR/Runtime boundary. Remaining engine-conversion work is therefore concentrated on non-trigger legacy execution surfaces and specialized event adapters, not on the 55-rule migration set.

This is an engine audit, not an identity-data completion report. Identity data remains intentionally deferred until the common engine and buff/debuff foundations are stable.

## Post-audit verification — 2026-09-20
The initial audit result above remains scoped to the compiled 55-rule set. A follow-up investigation verified the disputed probabilistic boundary and compatibility tests rather than treating the v92 failure as test-only.

- Current production probability callers construct `ProbabilisticTriggerRuntime` through `_probabilistic_trigger_runtime()` and pass that runtime into `_fire_probabilistic_trigger_event()`.
- The new-runtime path preserves `per_skill` activation buckets across repeated events and skill changes.
- v60/v61 once-per-turn behavior is now verified through production event handlers, with production RuleRuntime activation state reset at turn boundaries.
- Target-resolution failure is explicit: unresolved target markers are emitted, activation is preserved, and a state event-log trace is recorded when available.
- Full regression: **408 / 408 PASS**.

## Activation Ledger conversion — A (2026-09-20)

- Added `activation_ledger_v1.py` as the single mutable owner for production activation counts and scoped buckets.
- Added `BattleState.activation_ledger`; deepcopying a turn/probability branch therefore forks activation state with the rest of the state.
- Bound `ActivationRuntime` and `RuleRuntime` to the current `BattleState` ledger when a production context is supplied.
- Bound `ProbabilisticTriggerRuntime` to the same ledger. Its legacy `TriggerRule.activations` / `activation_buckets` fields are compatibility mirrors, not the production source of truth.
- Reworked probabilistic state signatures/restoration to snapshot/restore the ledger rather than treating `state.runtime` activation dictionaries as authoritative.
- Kept historical `state.runtime['probabilistic_trigger_*']` dictionaries as derived compatibility/trace snapshots only.
- Added `test_v112_activation_ledger.py` covering production RuleRuntime ownership, per-skill bucket persistence, and branch deepcopy isolation.
- Full regression after A: **411 passed**.

### A boundary still remaining

Legacy `TriggerRule` model fields and compatibility modules still expose mutable activation fields for migration/parity callers. They are not yet deleted because the remaining legacy surface has not been retired. This is an incremental ownership conversion, not a claim that all activation-related legacy code has already been removed.
