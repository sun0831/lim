# 0.7.100 — 받는 피해량 적용 주체 오판 수정

- 실제 원문 `받는 피해량 +X%`가 기존 parser에서 `dynamic_damage_bonus`로 컴파일되어 공격자 가하는 피해에 잘못 합산될 수 있던 문제 수정.
- `incoming_damage_bonus` 채널로 분리.
- `가하는 피해량 +X%`는 기존 outgoing `dynamic_damage_bonus` 유지.
- 혼합 문구(`받는 ... +25%, 가하는 ... +25%`)에서도 두 효과를 각각 분리.
- 42 targeted regression PASS.
- 주의: incoming_damage_bonus의 실제 적 공격 피해 적용 경로는 별도 target-side damage resolution 범위이며 이번 변경에서는 잘못된 outgoing 적용을 제거하는 데 집중.
