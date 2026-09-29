# E33 Special State Audit

- records: 54
- unique source texts: 54
- dedicated special-state runtime: **not required**
- contract gaps: **0**

## Classification
- skill_or_action_state: 13
- hp_stagger_state: 25
- resource_or_counter_state: 9
- turn_lifecycle_state: 4
- status_state: 3

## Routing

special_state is treated as a cross-cutting analysis axis. Named states, lifecycle transitions, resources/counters, HP/stagger, and skill/action state changes are routed through existing Condition/Effect/Trigger/Resource/Action/Skill primitives.
