# E-4 Buff/Debuff Aggregation Contract

## Purpose

E-4 makes stacking and modifier aggregation explicit without changing the existing default behavior for ordinary modifiers.

## Item stacking

`BuffDebuffRuntime.apply(..., stack_mode=...)` supports:

- `add`: potency/count and modifier values accumulate.
- `replace`: potency/count and modifier values are replaced.
- `max`: potency/count and each modifier value take the maximum.

## Modifier aggregation

Each buff/debuff may provide `modifier_policy`:

- `add` (default): additive aggregation.
- `max`: maximum active value.
- `min`: minimum active value.
- `replace`: highest `priority` wins; equal priority uses later application order.
- `multiply_scale`: opt-in multiplicative percentage scale, where 0.20 means x1.20.

A `default` policy may be supplied inside `modifier_policy`, with per-modifier keys overriding it.

## Important boundary

These policies are runtime mechanics, not claims about any specific Limbus Company status. Actual game rules should explicitly select the policy when a rule is migrated. Existing rules continue to use additive aggregation unless they opt into another policy.
