# Latest calculator handoff — 2026-09-21

## Current change
Calculator scenarios can treat `defense_level` as the target's effective Defense Level, separate from target `level`.
- `limbus_damage_engine_v29.py`: uses `state.runtime["defense_level_is_absolute"]` when enabled.
- `one_turn_solver_v29.py`: calculator scenario defaults this flag to true.
- Legacy/direct engine callers without the flag retain the previous level + defense_level behavior.

## Current Golden reference under investigation
Identity: 로보토미 E.G.O:: 눈물로 벼려낸 검
Skill: 아르카나 피어스 (S3)
- Deep Tears: 20
- Sword to Protect: 4 (clash power only; excluded from direct damage)
- Target Sinking: 4/1
- Attack Level: 68
- Defense Level: 67
- Vulnerable: none
- Clash-win bonus: none
- Coin displayed rolls: 13 / 17 / 21
- Observed cumulative damage: 28 / 65 / 110

## Important
The calculator's existing damage formula still does not reproduce this Golden observation. With the direct damage model currently in source, the same roll sequence is not yet 28 / 37 / 45. This remains an open Golden discrepancy; no value is being hardcoded to force a match.
