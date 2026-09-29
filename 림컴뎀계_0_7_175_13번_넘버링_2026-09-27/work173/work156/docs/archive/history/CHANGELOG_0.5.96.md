# 림컴뎀계 0.5.96 — named stack damage scaling

## 변경
- `N당 피해량 +X%` 형태의 명시적 누적 수치 기반 피해량 보정을 일반화.
- 기존 특수자원 목록에 포함된 자원은 기존 `resource_per` 경로를 유지.
- 목록에 없는 명명형 상태/자원은 `named_stack_per`로 처리하여 실제 `fighter.resources` 또는 `fighter.statuses`에서 현재 값을 읽음.
- `자신의 지령의 가호 1당 피해량 +2%` 같은 자기 자원형 조건 지원.
- `사랑/증오당 피해량 +2%` 같은 암시적 1당 조건 지원.
- `대상의 잔향 1당 피해량 +1%`처럼 대상 상태를 명시한 조건 지원.
- 최대값이 명시되면 피해 보정 상한 적용.
- 코인/대상별 실행 시점의 현재 상태를 읽으므로 선행 코인에 의한 상태 변화가 후속 코인 피해량에 반영됨.
- 기존 공격 가중치 피해 보정이 named-stack 정규식에 의해 오인식되지 않도록 우선순위 수정.

## 테스트
- 전체 pytest: **208 passed**
- 스킬 카탈로그 감사: 621 skills / 2,309 supported clauses / 1,729 unsupported clauses / **57.18%** clause support
- 신규 회귀 테스트: `test_v44_named_stack_damage.py`
