# 림컴뎀계 0.6.43 — Rule/Condition/Effect 공통 레지스트리 이관

## 이번 작업
- `ConditionRuntime`을 Condition IR의 단일 지원 연산자 레지스트리로 승격.
- `RuleMigrationRuntime.SUPPORTED_CONDITIONS`가 별도 중복 목록을 유지하지 않고 `ConditionRuntime.SUPPORTED_OPS`를 공유.
- `EffectRuntime`에 `GENERIC_EXECUTABLE_EFFECTS` 명시적 레지스트리와 `is_generic_executable()` 추가.
- `RuleMigrationRuntime._effect_state()`가 Effect category가 아니라 실제 공통 `EffectExecutor` 경로에서 실행 가능한 효과인지 레지스트리를 통해 판정.
- 따라서 `action`/`legacy` 같은 category에 속한다는 이유만으로 Rule IR 이관 대상이 되는 것을 방지.
- 기존 migration-safe / legacy compatibility 동작은 유지하고, 레지스트리 불일치에 대한 회귀 테스트를 추가.

## 검증
- migration 집중 suite: 31 passed
- 신규 registry consistency: 3 passed
- 전체 회귀: **345 passed**
- 이전 0.6.42 대비 테스트 342 → 345 (+3)

## 다음 단계
- 실제 `TriggerRule` 이벤트별 migration-safe 규칙을 shadow/golden 비교.
- parity가 확인된 generic Rule부터 실제 전투 경로에서 Legacy effect 처리 제거.
- 이후 Target/Action 계열 deferred effect를 공통 runtime으로 단계 이관.
