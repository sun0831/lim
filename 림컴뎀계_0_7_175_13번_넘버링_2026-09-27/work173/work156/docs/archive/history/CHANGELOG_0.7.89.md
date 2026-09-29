# 0.7.89 — 회귀 테스트 인프라 및 next-turn 적중 조건 정합화

## 수정
- `/tmp/v736/identity_catalog_v2.json` 고정 경로 제거 → 프로젝트 canonical `identity_catalog_v2.json` 사용
- A0 activation inventory 기대값을 현재 catalog 기준 73개로 정합화 (global 67 / per_turn 2 / per_target 2 / per_identity 1 / per_skill 1)
- E35 coverage 기대값을 현재 compiler/audit 결과 339 converted clauses / 30.73%로 정합화
- `1코인 [적중시] 다음 턴에 취약 1 부여` 계열의 next-turn 상태 효과가 `다음 턴` 필터에 의해 버려지던 문제 수정
- next-turn 상태 효과는 `AddNextTurnTargetStatus`로 예약하고 deferred causal effect로 보존하여 다음 턴에 현재 이벤트 대상을 대상으로 적용

## 검증
- 관련 6개 테스트: 6 PASS
- 추가 parser/compiler 회귀는 별도 수행

## 회귀 결과
- 수정 범위 관련 회귀: 101 PASS / 0 FAIL
- 전체 pytest: 180초 제한으로 완료되지 않음
- `-x` 전체 회귀: 60초 제한 전까지 54% 구간까지 진행되었고 새 실패는 확인되지 않음
