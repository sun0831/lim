# 림컴뎀계 0.5.2

### Release focus
**User-defined 1-turn damage-cycle simulation with a separate special-gimmick layer.**

### Implemented
1. Duplicate passive variants are execution-selected instead of double-stacked.
2. Special gimmick registry introduced for action-spawning mechanics.
3. Catalog-confirmed `원호 공격` pattern can enqueue a follow-up skill immediately after its trigger skill.
4. Last-ammo percentage extra-damage hook added as a secondary-damage event.
5. Coin-local ammo spending and several high-impact coin modifiers are connected to skill data.
6. Stagger damage is tracked separately from HP damage.
7. Results expose generated actions and special-gimmick traces.

### Validation
- 8 tests passed.
- 184 identities load from `identity_catalog_v2.json`.
- Special-gimmick audit report: `special_gimmick_report_v1.json`.

### Accuracy policy
Unsupported special mechanics are not silently approximated. They remain explicit so future implementations can be validated independently.
