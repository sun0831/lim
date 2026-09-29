# E20 — Resource Primitive / Trigger Catch-all Audit

## Scope

Based on E19's 215 `resource_transform` records and the 345 `trigger` candidates, E20 does four things:

1. Reclassifies the 345 trigger catch-all candidates by output shape.
2. Adds the missing highest-resource target selector as the symmetric counterpart to lowest-resource selection.
3. Adds a primitive for resource consumption used as a trigger without a cumulative reward.
4. Adds a primitive for resource-triggered skill replacement, kept distinct from `SKILL_RECLASSIFY`.

The classifier is deliberately conservative. A classification result is an audit/normalization result, not proof that the corresponding game rule is executable end-to-end.

## Trigger reclassification

- Trigger candidates: **345**
- Unique trigger source texts: **296**
- Resource gain: **92**
- Status/effect: **69**
- Action trigger: **67**
- Condition-only: **24**
- Unresolved: **93**

The `condition_only` bucket is retained because some clauses contain a predicate but no detectable output in the same source sentence. They should be joined to the following effect clause rather than fabricated into a Runtime effect.

## New/expanded ResourcePrimitive declarations

- `HIGHEST_RESOURCE_TARGET = highest_resource_selector`
- `RESOURCE_CONSUME_TRIGGER = resource_consume_trigger`
- `RESOURCE_TRIGGERED_SKILL_SWAP = resource_triggered_skill_swap`

`SKILL_RECLASSIFY` remains separate: it describes a skill being treated as a particular skill category/tag, while `RESOURCE_TRIGGERED_SKILL_SWAP` describes the actual replacement of one skill with another.

## Non-resource/special review

The E19 86-record unresolved/non-resource bucket contains at least two duplicate occurrences of:

`기본 공격 스킬과 합 가능 반격 스킬이 충전 횟수를 얻는 스킬로 취급됨`

This is compatible with `SKILL_RECLASSIFY` semantics and therefore should not be counted as a genuinely new resource primitive merely because E18's regex pass missed it.

The remaining cases require clause-level semantic review and are not force-mapped in E20.

## Deliberate exclusions

The 149 `status_effect_side_clause` candidates remain outside the resource audit and belong to Buff/Status Runtime work.

No identity-specific implementation was added in E20.
