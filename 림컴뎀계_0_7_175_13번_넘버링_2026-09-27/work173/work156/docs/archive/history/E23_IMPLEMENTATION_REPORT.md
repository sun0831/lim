# E23 — skill_transform audit and primitive boundary

## Source
- Base: 림컴뎀계_0.7.0_E22.zip
- Gap source: GIMMICK_GAP_REPORT_v4.md.json

## Important count correction
The full gap corpus currently contains **26 records** tagged `skill_transform`, not 22. The previously cited 22 is therefore treated as a subset/earlier filtered count and is not used as the E23 denominator.

## Clause audit
The 26 records produced 66 skill-related clause candidates under conservative line-level decomposition.

| classification | count |
|---|---:|
| unresolved | 31 |
| conditional_skill_trigger | 15 |
| true_skill_swap | 6 |
| skill_reclassify | 5 |
| next_turn_skill_swap | 4 |
| forced_or_followup_skill | 3 |
| coin_or_power_transform | 2 |

Counts overlap at record level but clause audit rows are individual candidate clauses.

## Architectural conclusion
`skill_transform` must not become a single runtime. The audit shows at least four separable primitives:

1. `SKILL_SWAP`: actual replacement of one skill with another.
2. `SKILL_RECLASSIFY`: a skill is treated/as-counted as another category.
3. `FORCED_OR_FOLLOWUP_SKILL`: an additional/forced skill action.
4. `COIN_OR_POWER_TRANSFORM`: coin/power alteration without replacing the skill.

`NEXT_TURN_SKILL_SWAP` is not a separate primitive: it is `SKILL_SWAP` plus a next-turn timing condition/state.

Likewise `RESOURCE_TRIGGERED_SKILL_SWAP` should be treated as a composition of a resource condition + generic `SKILL_SWAP`, rather than making resource ownership the fundamental skill-transform abstraction.

## Implementation
Added `ResourcePrimitive.SKILL_SWAP` and declarative mapping from EffectIR kind `skill_swap`.
Existing `RESOURCE_TRIGGERED_SKILL_SWAP` remains for compatibility and can be represented compositionally later.

## Tests
E23 focused tests: **3 passed**.

The full repository suite is not reported as fully passed in this stage because the previous environment showed a long-running/timeout condition during the complete suite; no unsupported claim is made here.
