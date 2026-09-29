# Charge Overflow Rule Implementation — 2026-09-22

## Scope

This change implements two source-backed Charge-over-cap clauses:

1. Formation-first ally overflow: overflowed Charge Count grants next-turn Charge Field 1 per overflow, capped at 3, including E.G.O skills.
2. Same-skill overflow damage: overflowed Charge Count grants that skill +3% damage per overflow, capped at 15%.

## Runtime boundary

- `ResourceRuntime.set()` emits `resource_overflow` with owner identity and skill id when a declared resource maximum is exceeded.
- `GimmickRegistry` compiles the formation-first support clause from passive text as `charge_overflow_next_turn_field`.
- `event_runtime_v1.after_resource_event()` consumes `resource_overflow` and writes the result to `next_turn_state` rather than mutating current-turn Charge Field.
- `OneTurnSolverV29._resolve_action()` reads only the active passive source text for the explicit same-skill damage clause and converts this action's own Charge overflow into a dynamic damage modifier.

## Caps and semantics

- Charge Count itself remains clamped to its declared maximum.
- Overflow is preserved as an event value; it is not added to Charge Count.
- Next-turn Charge Field is capped at 3 per triggering overflow event.
- Same-skill damage bonus is capped at 15% (5 overflow counts × 3%).
- Turn-end Charge Count decay is unchanged and does not create overflow.
- No `Charge Potency` conversion is introduced by this change.

## Verification

- Targeted regression: 143 passed.
- Direct solver fixtures verified both next-turn Charge Field and same-skill damage bonus behavior.
