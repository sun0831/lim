# 림컴뎀계 0.5.48

## Stagger legacy Trigger queue bridge

- Legacy/catalogue passive `trigger: Stagger` effects now support `queue_action` in the probabilistic branch runtime.
- Previously these passives could apply ordinary state effects but silently drop generated follow-up actions.
- `queue_action` now resolves by `identity_id` + `skill_id`, with skill-name fallback, and is inserted into the same branch-local generated-action chain.
- Non-queue legacy Stagger effects continue to use the existing DamageEngine effect application path.
- Existing `after_stagger` TriggerRuntime behavior, branch-local state propagation, recursive generated-action depth limits, and coin-level trigger handling are unchanged.

## Verification

- 102 tests passed.
- Python syntax check passed.
