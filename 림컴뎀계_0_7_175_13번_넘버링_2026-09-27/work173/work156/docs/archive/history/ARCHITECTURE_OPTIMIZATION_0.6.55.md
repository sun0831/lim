# 림컴뎀계 0.6.55 — Production Legacy Execution Retirement

## 목적
0.6.54의 Legacy 실행 비진입 검증을 실제 production migration boundary에서 fail-fast 정책으로 강화한다.

## 변경
- `RuleMigrationRuntime.production_fire()`는 더 이상 `TriggerRuntime`으로 fallback하지 않는다.
- production 이벤트에 deferred Rule이 섞이면 `RuntimeError`로 즉시 중단한다.
- Legacy runtime은 compatibility/test 경로로만 유지한다.
- `status_gain_affiliation_ordered`를 공통 `EffectExecutor`가 직접 실행하도록 이관했다.
- Blade Lineage의 battle-start ordered affiliation status effect가 production Rule IR에서 직접 처리된다.
- 기존 `status_gain_affiliation_ordered` 수동 Legacy 처리 경로는 catalog production에서 더 이상 필요하지 않으며 compatibility 코드로만 남긴다.

## 검증
- 현재 catalog TriggerRule: 55
- migration-safe: 55
- deferred: 0
- unknown: 0
- 전체 회귀: 377 passed
- Blade transfer integration: PASS
- Legacy retirement boundary: PASS

## 의미
이번 버전부터 production에서 Generic Rule이 Legacy TriggerRuntime으로 조용히 내려가는 fallback 자체가 구조적으로 차단된다. 새 Rule이 generic-safe가 아니면 즉시 migration 작업 대상으로 드러난다.
