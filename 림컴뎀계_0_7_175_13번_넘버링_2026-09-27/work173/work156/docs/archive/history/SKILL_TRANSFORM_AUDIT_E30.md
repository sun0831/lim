# E30 Skill Transform Audit

## Scope
E23 skill-transform corpus: 26 records / 66 clauses.

## Decision
No new monolithic `SKILL_TRANSFORM_RUNTIME` is required. Existing/common routes are reused:
- `SKILL_SWAP` for actual replacement
- `SKILL_RECLASSIFY` for classification/interpretation changes
- Skill event Trigger/Action for conditional skill events and forced follow-up actions
- Coin/Power Transform for coin or power changes
- Status/State Runtime for non-skill state changes

`SKILL_SWAP` needs parameter-level support for slot selection, retry after invalidation, and deferred next-turn timing.

Unresolved clauses remain unresolved rather than being guessed.
