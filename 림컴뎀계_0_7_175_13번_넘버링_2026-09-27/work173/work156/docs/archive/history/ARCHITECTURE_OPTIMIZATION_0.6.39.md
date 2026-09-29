# 림컴뎀계 0.6.39 — Migration Safety Gate

## 이번 사이클
- Legacy TriggerRule → Rule IR migration safety gate를 추가했다.
- Effect 종류만 generic인지 보는 기존 판정에서 벗어나, Rule IR 조건 연산자가 공통 ConditionRuntime에서 지원되는지도 함께 검사한다.
- 지원되지 않는 조건이 포함된 Rule은 migration-safe로 취급하지 않는다.
- generic resource/status effect에 명시적 대상이 없을 때 Legacy 규칙의 owner를 기본 대상 후보로 전달한다.
- migration activation budget은 조건/target 검사를 통과하고 IR execution이 시작된 뒤 소비하도록 정리했다.
- target resolution 실패로 legacy activation 횟수가 소모되는 경로를 차단했다.
- 실제 전투 경로는 이번 버전에서 강제 전환하지 않는다. 기존 339개 회귀 테스트를 유지하면서 migration boundary 자체의 안전성을 강화했다.

## 실제 검증
- 전체 테스트: 342 passed
- 카탈로그 184 인격 기준 compiled TriggerRule: 55
- fully generic effect rule: 20
- deferred rule: 35
- unknown rule: 0

## 다음 단계
- safety-safe Rule 중 실제 이벤트별 실행 경로를 골라 shadow/golden 비교
- 동일 결과가 확인된 Rule부터 Legacy handler 제거
- Target/Action 계열 deferred effect의 공통 runtime 이관
