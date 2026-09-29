# 림컴뎀계 0.6.44 — Rule IR 실제 실행 경계 이관

## 이번 변경

0.6.43에서 정리한 Rule/Condition/Effect registry를 실제 `GimmickRegistry` 이벤트 실행 경계에 연결했다.

### 실행 경로

```text
TriggerRule
  -> migration_safe()
  -> Rule IR
  -> ConditionRuntime
  -> TargetRuntime
  -> EffectRuntime
  -> EffectExecutor
```

migration-safe가 아닌 규칙은 기존 `TriggerRuntime`을 계속 사용한다.

## 실제 이관된 이벤트

- `battle_start`
- `turn_start`
- `after_clash`
- `after_coin`
- `after_skill`
- `after_kill`
- `after_received_attack`
- `resource_cumulative_consumed`

기존 `fire_event()` 공개 호환 경로는 변경하지 않았다.

## 중요 호환성 처리

- Legacy TriggerRule activation budget은 기존 객체가 계속 소유한다.
- generic rule은 공통 `EffectExecutor`에서 1회만 실행한다.
- deferred rule은 Legacy `TriggerRuntime`에서 실행한다.
- generic 실행 후 callback에서 동일 effect를 다시 적용하지 않도록 `executed_generic` 경계를 사용한다.
- runtime target resolution 실패 시 migration path가 compatibility payload를 반환한다.
- `충전`, `탄환`, `호흡` 등 core resource는 `ResourceRuntime`의 기존 core-attribute 매핑을 사용한다.
- extra trigger rule의 `activation_scope`/`source_text` positional mapping 오류를 수정했다.

## 전체 데이터 기준 현재 분류

`identity_catalog_v2.json`의 184 인격을 모두 빌드해 `GimmickRegistry`를 구성한 기준:

- TriggerRule: **55**
- migration-safe: **20**
- deferred: **35**
- unknown: **0**
- effect instances: generic **21**, deferred **36**

이는 "전체 인격 구현률"이 아니라 현재 TriggerRule migration 대상의 실행 가능성 측정값이다.

## 검증

- migration focused suite: **33 passed**
- full pytest: **347 passed**
- test files: **125**
- exact duplicate body groups: **1**

## 다음 이관 대상

현재 일반 `GimmickRegistry` 경로는 migration-safe TriggerRule을 공통 Runtime으로 실행한다.

다음 단계는 확률/분기 실행 경로(`one_turn_solver_v29`의 probabilistic generated-action path)에서도 동일한 migration boundary를 적용하고, 그 후 실제 20개 generic rule에 대한 golden parity를 추가하는 것이다.
