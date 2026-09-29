# 림컴뎀계 0.5.90

## Target metadata propagation + per-target last-ammo extra damage

- Triggered/generated `ActionRequest` target metadata now takes precedence over action/scenario defaults.
  - `target_policy`
  - `target_index`
  - `target_ids`
- This fixes generated follow-up attacks that carry their own target selector but previously inherited the scenario selector.
- Last-ammo secondary damage logging now records `target_id`.
- Existing explicit multi-target execution remains target-local: each selected `EnemyState` is resolved independently.
- Regression suite: 189 passed.
