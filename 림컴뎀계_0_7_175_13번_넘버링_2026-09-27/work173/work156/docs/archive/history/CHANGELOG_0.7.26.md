# 0.7.26 — 진동 조건 보강 + 보호막 회귀 수정

- `대상의 진동이 N 이상이면`을 일반 Tremor potency 조건으로 연결.
- 기존 일반 Status threshold parser가 같은 문장을 Tremor count 조건으로 중복 해석하던 문제 수정.
- `대상의 진동이 5 이상이면 대상의 합 위력 -1` 패턴을 공통 `StatusThreshold + ModifyContext(clash_power_bonus)`로 검증.
- `AddShield`에 총량 제한/회당 제한을 구분하는 `cap_total` 추가.
- 충전 위력 기반 전투 시작 보호막의 최대치가 실제 `최대 N`을 사용하도록 수정.
- 피격 직전 보호막처럼 `턴당 여러 번` 누적되는 회당 제한 효과는 회당 cap으로 처리.

## Verification

- Tremor/related tests: 35 passed.
- Full suite remains subject to pre-existing unrelated failures in activation inventory and legacy gimmick coverage.
