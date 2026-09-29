# 0.7.94 — Attack/Defense Power Up/Down 원문 범위 오판 수정

## 확정 오판
원문 정의상 Attack Power Up/Down은 Attack Skill Final Power에만,
Defense Power Up/Down은 Defense Skill Final Power에만 적용되어야 한다.
기존 공통 `skill_power` modifier는 스킬 종류 범위가 없어 양쪽 스킬에 적용될 수 있었다.

## 수정
- status catalog에 `skill_scope: attack|defense` 추가
- BuffDebuffRuntime이 skill context의 `skill_is_defense`를 기준으로 범위 필터링
- StatusEffectRuntime이 catalog의 skill_scope를 modifier policy로 전달
- 일반 Power Up/Down은 기존대로 attack/defense 공통 Final Power 유지

## 검증
- `test_status_scope_audit.py`: 3 PASS
- 관련 status/damage regression: 68 PASS
