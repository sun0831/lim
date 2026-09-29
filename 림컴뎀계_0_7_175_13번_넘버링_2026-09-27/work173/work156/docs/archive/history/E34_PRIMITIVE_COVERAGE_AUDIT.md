# E34 — Primitive Coverage Audit

## Purpose

Compare the E17-E33 audit axes with the canonical E34 Primitive Registry and verify that recurring semantics route to existing common contracts rather than creating one runtime per axis.

## Result

The registry keeps the 13 resource primitives frozen and adds declarative common contracts for Condition, Target, Effect/Status, Action, Trigger, Skill, Damage Modifier, and Lifecycle semantics already implemented by existing modules.

These entries are **contracts/routing IDs, not new Runtime classes**.

### Axis routing

- E18 resource_transform: Resource + Condition + Target + Status/Effect + Skill contracts.
- E23 skill_transform: `skill_swap_timed`, `skill_reclassify`, `forced_followup_action`, `coin_power_transform`.
- E24 non_resource_special: State/Condition/Action/Target/Skill/Status contracts.
- E26 status_effect_side_clause: `status_effect`, `buff_debuff_effect`, `status_lifecycle`, plus Condition/Target composition.
- E27 cross_identity: `affiliation_target_selector`, `specific_identity_target`, `target_relation_selector`, Condition/Resource/Status/Action composition.
- E28 target_selection: explicit/random/count/speed/HP/formation/status/affiliation/specific-identity/relationship selectors.
- E29 stack_threshold: `condition_threshold`, `condition_resource_predicate`, `activation_limit`, and existing status/resource predicates.
- E30 skill_transform: `skill_swap_timed`, `skill_reclassify`, `forced_followup_action`, `coin_power_transform`, `status_lifecycle` where state is involved.
- E31 multi_target: `target_count` + target selector composition.
- E32 probability_random: `random_target` + `probabilistic_trigger`; per-coin randomness remains a RuleIR parameterization gap.
- E33 special_state: State/Condition/Resource/Status/Skill/Turn lifecycle composition.

## Deliberate exclusions

No dedicated runtime was introduced for cross_identity, target_selection, stack_threshold, multi_target, probability_random, or special_state. The audit evidence did not justify one.

The E34 registry also does not claim that every catalog clause is fully executable. Unsupported/identity-specific/compound clauses remain represented as migration/audit gaps until E35 RuleIR compilation and later data integration validate them.
