# 0.5.89 — Attack-weight target scaling

- Preserve catalog `weight` as `SkillData.attack_weight`.
- Default action target count to explicit action/scenario target count; otherwise use skill attack weight.
- Support exact skill-level patterns where missing targets relative to attack weight increase damage by a stated percentage per target.
- Support exact one-target damage scaling patterns.
- Evaluate these modifiers from the action's resolved target count at damage timing.
- Added regression tests for parser and dynamic modifier behavior.

Validation: 188 tests passed.
