# 0.5.88 — explicit multi-target enemy states

- Added independent enemy target states when `enemy.targets` is supplied.
- Unopposed attacks can resolve the same skill/coin sequence against multiple selected targets without multiplying damage after the fact.
- Added per-action `damage_by_target`, target resolution events, and final `target_states` (HP/stagger/statuses).
- Preserved legacy `target_count` aggregate behavior when explicit enemy target slots are not supplied.
- Added regression coverage for independent target HP and multi-target damage accounting.
