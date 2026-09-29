# 림컴뎀계 0.6.28

## Generic Damage Modifier Runtime

- `damage_modifier_runtime_v1.py` 추가
- 피해 증가/감소 계열을 공통 Runtime에서 관리하도록 구조화
- 현재 지원 modifier:
  - `damage_percent`
  - `critical_damage_percent`
  - `flat_damage`
- 공격 유형, 크리티컬 여부, 스킬명, 대상 인격 조건 지원
- 소속/인격 기믹은 modifier를 등록하고 실제 적용은 DamageEngine이 담당

## 검계 본국검술 서포트

- `본국검술` 서포트의 전투 시작 효과를 공통 DamageModifierRuntime으로 연결
- 호흡을 가장 많이 보유한 아군 1명 선택
- 해당 아군의 참격 크리티컬 피해량 +15%
- 검계 인격으로 대상 제한하지 않고 카탈로그의 '아군 1명' 조건 그대로 처리
- 등록 이벤트를 `event_log`에 기록

## Verification

- 전체 테스트: **301 passed**
- Python syntax check: PASS
