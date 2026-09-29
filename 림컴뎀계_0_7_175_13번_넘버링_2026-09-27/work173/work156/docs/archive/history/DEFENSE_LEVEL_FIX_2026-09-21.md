# Defense Level input fix — 2026-09-21

- Calculator target `level` and `defense_level` are separate inputs.
- Damage calculation now uses `defense_level` as the effective Defense Level.
- `enemy.level` is no longer added to `enemy.defense_level`.
- Defense Level Down / bonuses remain additive to the effective Defense Level.
- This change is specifically to prevent a target level 65 + defense level 67 from being interpreted as Defense Level 132.

Golden reference currently being checked:
- S3 `아르카나 피어스`
- 깊은 눈물 20
- 지키는 검 4 (clash power only; no direct damage bonus)
- target Sinking 4/1
- Attack Level 68
- Defense Level 67
- no Vulnerable
- no clash-win bonus
- observed cumulative damage: 28 / 65 / 110
