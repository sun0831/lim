# 림컴뎀계 0.6.34 — Effect Execution Boundary

## 목표
Rule IR을 단순한 검사/변환 계층에서 실제 공통 전투 상태 변경까지 연결하는 첫 단계.

## 변경
- `effect_executor_v1.py` 추가
  - state/flag
  - resource gain/consume/set/convert
  - status gain/lose/set
  - damage modifier 등록
- `RuleRuntime.execute()` 추가
  - `evaluate()` 결과의 EffectCommand를 공통 executor로 실행
  - support/assist/extra/legacy effect는 전문 runtime으로 넘길 수 있도록 deferred command 유지
- 기존 `evaluate()` 동작은 변경하지 않음.
- ResourceRuntime / DamageModifierRuntime을 재사용하여 계산 로직 중복을 피함.

## 검증
- 전체 테스트: 327 passed
- 신규 executor 테스트: 3개
- 기존 테스트 회귀 없음

## 다음 최적화 대상
1. Effect executor의 target 다중 적용
2. status/resource mutation 이벤트를 공통 EventLog 형식으로 정규화
3. legacy effect별 migration coverage 측정
4. 실제 gimmick module 일부를 RuleRuntime.execute 경로로 이동
5. Golden Test를 Rule IR 실행 결과와 직접 연결
