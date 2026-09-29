# E26 — Status Side Clause Audit

- Resource-transform source records: 215
- Status side clause candidates: **149**
- Unique clause texts: **129**

## Routing counts
- `status_effect_or_effect`: 85
- `buff_debuff_modifier`: 25
- `status_effect`: 21
- `target_or_action_compound`: 12
- `skill_or_classification`: 6

## Scope
- These 149 candidates are removed from the Resource Runtime scope and routed to the Buff/Status audit.
- Routing categories are conservative and may identify compound clauses; they are not claims that the entire clause is already executable.
- No new Status Runtime primitive is introduced in E26. Existing catalog/runtime is reused; unresolved identity-specific semantics remain explicit.
