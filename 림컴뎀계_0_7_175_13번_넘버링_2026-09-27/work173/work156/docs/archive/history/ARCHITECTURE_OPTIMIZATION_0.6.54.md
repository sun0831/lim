# 림컴뎀계 0.6.54 — Legacy Execution Retirement Boundary

## 목표
0.6.53에서 현재 catalog의 TriggerRule 55개가 모두 Rule IR/공통 Runtime으로 migration-safe가 되었으므로, 실제 전투 실행 경로에서 동일 Rule이 Legacy TriggerRuntime으로 다시 실행되는 중복 경로를 차단한다.

## 변경
- `RuleMigrationRuntime.partition()` 추가
  - event별 Rule을 IR-owned / legacy-only로 단일 분류
- `RuleMigrationRuntime.production_fire()` 추가
  - production 실행의 단일 migration boundary
  - migration-safe Rule은 `fire_migrated()`만 실행
  - deferred Rule만 Legacy TriggerRuntime으로 fallback
  - fallback 개수를 관측 가능하게 반환
- `GimmickRegistry._fire_migrated_event()`가 production boundary 사용
- `GimmickRegistry._last_legacy_fallback_count` 추가
- probabilistic trigger path도 동일한 `partition()`을 사용
- Legacy `TriggerRuntime`은 외부 호환/Parity용으로 유지하지만 현재 catalog generic Rule의 production 실행 경로에는 사용되지 않음

## 검증
- migration-safe catalog Rule: 55/55
- production catalog event fallback: 0
- Legacy retirement boundary tests: 3 passed
- 전체 회귀: 375 passed

## 의미
이번 버전의 목적은 Legacy 코드를 즉시 삭제하는 것이 아니라, 먼저 **실행 의존성**을 끊고 이를 테스트로 고정하는 것이다. 이후 충분한 기간 동안 parity/regression이 유지되면 compatibility-only Legacy 코드와 관련 테스트를 별도 단계에서 제거할 수 있다.
