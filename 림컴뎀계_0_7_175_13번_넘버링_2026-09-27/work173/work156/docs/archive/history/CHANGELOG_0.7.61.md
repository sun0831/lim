# 0.7.61 — 상대적 편성 순서 Target Selector 정합화

- `자신보다 편성 순서가 빠른 아군` → `formation_before_owner`
- `자신보다 편성 순서가 느린 아군` → `formation_after_owner`
- `자신보다 편성 순서가 빠른 아군 중 충전 횟수가 낮은 아군` → `formation_before_owner_charge_min`
- 기존 `formation_min/max`와 분리하여 절대 순위와 상대 순위를 혼동하지 않음.
- 실제 identity-182 원문 패턴을 근거로 경계를 추가했으며, identity-182 전체 패시브 실행을 의미하지 않음.

검증: 105 PASS / 0 FAIL
