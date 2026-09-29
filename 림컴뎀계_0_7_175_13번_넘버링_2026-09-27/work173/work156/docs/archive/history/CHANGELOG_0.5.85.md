# 0.5.85 — Status Burst / Resource-Cost Coin Power

## Changes
- Added conservative parsing and execution for explicit `진동 폭발` effects.
  - Uses current Tremor Potency as fixed damage.
  - Consumes 1 Tremor Count.
  - Emits a structured `status_burst` event.
- Added conservative parsing and execution for explicit `화상 발동`, `파열 발동`, and `침잠 발동` coin effects using the same current-status trigger model.
- Added parsing for explicit resource consumption coupled to skill-wide Coin Power, e.g. `충전 횟수를 10 소모하여 코인 위력 +2`.
  - Resource consumption is applied at action start.
  - The resulting Coin Power modifier is attached to the skill condition model.
- Added regression tests for status burst and resource-consumption/Coin-Power parsing.

## Validation
- pytest: 178 passed
- Attack skills audited: 621
- Parser clauses: 2,205 supported / 1,833 unsupported
- Parser clause coverage: 54.61%

Unsupported-clause counts are parser-clause counts, not counts of broken skills. Ambiguous effects remain unsupported rather than being guessed.
