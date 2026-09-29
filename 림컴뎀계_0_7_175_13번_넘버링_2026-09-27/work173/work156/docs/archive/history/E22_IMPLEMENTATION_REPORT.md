# E22 — Resource Consumption Trigger Audit

## Scope
Audited the 92 `resource_consume` clause candidates from the E18 decomposition. The goal is to distinguish cumulative-spend rules, actual consumption-triggered downstream effects, direct consumption effects, conversions, tracking/modifier rules, and pure conditions. This is a semantic audit, not proof of end-to-end runtime execution.

## Results
- Input resource-consumption clauses: **92**
- `cumulative_spend_reward`: **13** — maps to existing `CUMULATIVE_SPEND_GAIN`.
- `consume_trigger`: **15** — genuine consumption-event → downstream-effect candidates for `RESOURCE_CONSUME_TRIGGER`.
- `consume_conversion`: **6** — consumption causes a new resource/state/skill outcome; represented as a composition of consume + effect/transform and requires case-level validation.
- `consume_during_action`: **23** — resource consumption is part of an action/coin rule; not a standalone trigger primitive.
- `direct_consume_effect`: **15** — explicit consume operation with immediate effect; existing Effect runtime owns the consume operation.
- `consume_tracking_modifier`: **13** — consumed amount is reused as a parameter/modifier; not a new primitive by itself.
- `consume_condition`: **7** — consumption is a predicate/fallback condition; should route through Condition/Target/Effect rather than become a standalone consume trigger.

## Important conclusion
The 92 records must **not** be interpreted as 92 missing `RESOURCE_CONSUME_TRIGGER` implementations. Only 15 are clean trigger candidates. The remaining records are compositions or existing Effect/Condition responsibilities.

`RESOURCE_CONSUME_TRIGGER` therefore remains useful, but E22 does not expand it blindly. Its schema should remain composable: consumption event + trigger timing + downstream effect + optional activation limit/amount reference.

## Tests
E22 audit tests: **4 passed**.
