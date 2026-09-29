# A0-A1 Activation State Audit

## Scope
This audit is performed **before** removing `TriggerRule.activation_buckets` or solver sync/restore code.
The purpose is to freeze current behavior and measure real catalog impact first.

## A0: seven-scope characterization

Covered scopes:

1. global
2. per_identity
3. per_actor
4. per_skill
5. per_target
6. per_identity_target
7. per_actor_target

`test_activation_scope_parity_a0.py` contains:
- 7-scope parity fixtures under a normal production-style context.
- explicit `per_actor_target` budget isolation coverage.
- explicit characterization of the known actor_id-only fallback discrepancy.
- explicit dual-budget (`turn_cap`) characterization.

Targeted result: **11 passed**.

## A1: actual catalog impact

The current `identity_catalog_v2.json` + `GimmickRegistry` build produces **55 trigger rules**.

Activation scopes in the actual compiled catalog:

| Scope | Rules |
|---|---:|
| global | 49 |
| per_identity | 1 |
| per_skill | 1 |
| per_target | 2 |
| per_actor | 0 |
| per_actor_target | 0 |
| per_identity_target | 0 |
| per_turn (legacy/source-side scope) | 2 |

The seven canonical scopes therefore have **0 current catalog rules using per_actor or per_actor_target**. Their contracts still require tests because they are runtime API capabilities and future migrated rules may use them.

Two current compiled rules carry `metadata.turn_cap`:
- `gimmick:38`: per_target, limit 1, turn_cap 1
- `gimmick:39`: per_target, limit 1, turn_cap 2

A direct eligibility comparison over those rules found **0 mismatches** between current `TriggerRule.eligible()` and `ActivationLedger.eligible()` for representative bucket/count states.

## actor_id fallback finding

There is a real structural discrepancy in the two implementations:

- `TriggerRule._scope_key()` for `per_actor` / `per_actor_target` falls back from `trigger_identity_id` to `identity_id` and does **not** use `actor_id`.
- `ActivationLedger.scope_key()` and `ActivationRuntime._scope_key()` allow `actor_id` as a fallback.

The actor_id-only characterization reproduces this discrepancy for both scopes.

Static inspection of the current production code found no existing call site that supplies an actor_id-only activation context to these scope calculations. Therefore the **current catalog impact is 0 observed cases**, but the API contract remains inconsistent and must be resolved before the mirror counters are removed.

## Important non-conclusion

No game-rule decision is made here about whether `actor_id` or `identity_id` is semantically correct for future `per_actor` rules. That decision remains an A2 contract decision, not an assumption hidden inside the refactor.
