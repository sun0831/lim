# 림컴뎀계 0.6.49 — queue_action ActionQueue migration

## 목적
Rule IR migration-safe Effect 중 `queue_action`을 Legacy compatibility payload에서 공통 ActionQueue 실행 경계로 이관한다.

## 변경
- `EffectRuntime.GENERIC_EXECUTABLE_EFFECTS`에 `queue_action` 등록
- `RuleMigrationRuntime`이 action category의 generic executable effect를 migration-safe로 분류
- `EffectExecutor._queue_action()` 추가
  - live `ActionQueue` + source `ActionRequest`가 있으면 `ActionQueue.triggered_from()`으로 생성
  - `identity_id` / display-name identity 모두 해석
  - `skill_id` / `skill_name` 모두 지원
  - target/coin target/trigger metadata 전달
  - live queue context가 없으면 deferred 처리하고 activation을 소비하지 않음
- `GimmickRegistry._fire_migrated_event()`가 TurnState runtime의 action boundary를 자동 참조
- solver가 `TurnState.runtime`에 `action_queue`, `identity_map`, `current_action_request`를 노출
- after_skill뿐 아니라 after_clash / after_coin / after_received_attack 등 동일 migration 경계에서 queue_action 사용 가능

## catalog migration 상태
- TriggerRule: 55
- migration-safe: 32
- deferred: 23
- unknown: 0
- safe Effect 구성:
  - resource_gain 17
  - queue_action 10
  - resource_gain_affiliation_count 2
  - status_potency_damage 1
  - extra_damage_scale 1
  - resource_consume 1
- deferred Effect 구성:
  - support_action 6
  - resource_gain_lowest_allies 2
  - poise_gain_lowest_ally 2
  - heal_lowest_ally 2
  - poise_gain_lowest_affiliation 2
  - register_fatal_prevention 2
  - 기타 특수 Effect 7

## 테스트
- 전체 테스트: **361 passed**
- queue_action 전용/runtime integration 테스트 추가
- catalog 32개 migration-safe Rule Golden parity 유지
- 기존 전체 회귀 PASS

## 다음 우선순위
`support_action`을 SupportActionResolver + ActionQueue 공통 Effect로 이관한다. `requested_next` 같은 formation-relative skill selection은 기존 resolver semantics를 그대로 사용하고, 일반 `queue_action`과 동일한 generated-action attribution을 유지한다.
