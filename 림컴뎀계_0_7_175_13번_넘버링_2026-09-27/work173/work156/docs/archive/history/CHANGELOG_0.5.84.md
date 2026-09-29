# 0.5.84 — batch damage-pattern expansion

- Added dynamic `충전당 피해량 +N% (최대 M%)` evaluation from current Charge.
- Added static `크리티컬 피해량 +N%` parsing into skill-level critical damage bonus.
- Added `이 스킬에서 소모할 탄환 N 당 기본 위력 +M` based on actual ammo consumed by the action.
- Preserved dynamic coin-time evaluation and existing one-turn state/trace architecture.
- Regression suite: 175 tests passed.
