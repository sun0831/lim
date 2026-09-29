# E-12 Status Effect → Damage Path

## Goal

Connect catalog-backed common status effects to the existing damage execution path without guessing compound mechanics.

## Value source rule

`StatusEffectRuntime.apply_catalog_effect()` now derives the applied strength from catalog semantics when `value` is omitted:

- damage/final/clash/coin-power style effects → `Count`
- offense/defense/crit/base-power style effects → `Potency`

This prevents the previous implicit `value=1` from silently collapsing multi-stack status values.

## Common execution path

`status_effect_catalog_v1.json`
→ `StatusEffectRuntime`
→ `BuffDebuffRuntime`
→ `DamageModifierRuntime`
→ `DamageEngine.coin_roll/static_modifier/dynamic_modifier`

Covered by E-12 tests for Damage Up, Power Up, Plus Coin Boost, Offense Level Up, Protection and Fragile.

Compound effects such as Dark Flame remain explicitly deferred.
