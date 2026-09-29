# A3/A4 Implementation Report — 2026-09-21

## Scope

A3 activation-state single ownership and A4 Solver sync/restore removal were applied to the full `0.7.0 E36 A0 strong` project.

## Contract

The canonical activation contract is:

`TriggerRule = definition`  
`ActivationLedger = mutable activation state owner`  
`ActivationRuntime / ProbabilisticTriggerRuntime / Solver = consumers of the Ledger`

Legacy `TriggerRule` behavior is **not** the contract. In particular, production behavior remains Ledger/Runtime semantics for actor fallback, `turn_cap`, and negative limits.

## A3 changes

- Removed mutable `TriggerRule.activations` state.
- Removed mutable `TriggerRule.activation_buckets` state.
- Kept constructor positional compatibility for old callers; the retired counter arguments are ignored and do not become runtime state.
- Removed `TriggerRule.eligible()`, `consume()`, and `reset_turn()` counter logic.
- `ActivationRuntime.eligible()` now delegates activation eligibility to `ActivationLedger.eligible()`.
- Removed duplicated `ActivationRuntime._scope_key()` implementation.
- `ProbabilisticTriggerRuntime` now always has an `ActivationLedger` and no longer falls back to mutating rule counters.
- Legacy compatibility runtime was changed to use its own Ledger rather than storing counters on rules.
- Golden parity harness was updated to compare Ledger state rather than rule-owned counters.

## A4 changes

Removed the Solver-side activation-state mirror path:

`Ledger -> TriggerRule.activation_buckets -> Ledger`

Specifically removed:

- `_sync_probabilistic_trigger_activation_state()`
- `_restore_probabilistic_trigger_activation_state()`
- all production call sites for those helpers
- mutation of `rule.activations` / `rule.activation_buckets` from Solver

Probabilistic branch state is already represented directly in `TurnState.activation_ledger` and `_probabilistic_state_signature()` / `_restore_probabilistic_state_signature()` continue to serialize/restore that Ledger state directly.

## A0 test adjustment

The A0 known-difference tests were removed after the A3 ownership decision because their purpose was to characterize differences between the retired Legacy counter and the production Ledger. The remaining A0 tests now verify the production contract directly:

- Ledger == ActivationRuntime
- 8 activation scopes
- semantic bucket-sharing matrix
- per-target turn cap
- per-actor-target isolation
- clone/snapshot round-trip
- catalog inventory
- Runtime has no duplicate scope-key implementation

A0 was reduced from 61 tests by removing the 7 `test_known_diff_*`/legacy-only cases.

## New A3/A4 tests

Added `test_activation_ownership_a3_a4.py` with 6 focused tests covering:

- TriggerRule definition-only state
- Ledger ownership
- no duplicate Runtime `_scope_key`
- Probabilistic runtime not mutating rules
- Solver sync/restore methods absent
- no activation counters in `TriggerRule.to_dict()`

## Validation

### Fast suite

`python run_tests.py --fast`

**654 passed, 9 deselected**

### Slow suite

All 9 slow tests were run individually and passed:

- A0 catalog activation inventory
- legacy compatibility catalog boundary
- common Runtime catalog safety
- two support-command catalog tests
- probabilistic after-clash state test
- infinite bleed terminal-count test
- joint bleed trim test
- catalog RuleIR golden parity

### Combined coverage count

**654 fast + 9 slow = 663 passed.**

The aggregate `pytest -q` invocation did not return within the execution timeout even though the fast set and all 9 slow tests were independently verified as passing. Therefore the 663 figure is based on the complete partitioned suite, not an uninterrupted single pytest process.

## Production-source status

Production code was changed in this A3/A4 pass. The final package contains the entire project source tree, not a changed-files-only patch.
