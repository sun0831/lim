# 림컴뎀계 0.6.45 — 확률/분기 Rule IR Migration Boundary

## 이번 변경

`one_turn_solver_v29`의 probabilistic generated-action 경로에 Rule IR migration boundary를 적용했다.

### 적용 경로

```text
Probabilistic TriggerRule
  -> migration_safe()
  -> Rule IR
  -> ConditionRuntime
  -> TargetRuntime
  -> EffectRuntime
  -> EffectExecutor
```

migration-safe가 아닌 Action/특수 Effect는 기존 probabilistic TriggerRuntime 경로를 유지한다.

## 적용 이벤트

- `after_clash`
- `after_hit`
- `after_coin`
- `after_stagger`
- generated action `after_skill`
- unopposed probabilistic action `after_skill`

초기 terminal-state의 기존 `after_skill` compatibility 경계는 기존 분기/생성-action 의미를 보존하기 위해 Legacy 경로를 유지한다.

## Branch State activation 개선

확률 분기에서 Rule activation을 상태축으로 유지하도록 확장했다.

- `probabilistic_trigger_activations`
- `probabilistic_trigger_activation_buckets`
- `global` 및 scoped activation 상태 보존
- migrated generic Rule은 branch state activation을 권위값으로 사용
- deferred Legacy Rule은 기존 runtime-local activation semantics 유지

따라서 Rule IR migration 때문에 확률 분기 사이의 activation budget이 임의로 초기화되지 않는다.

## EffectExecutor 보정

`set_flag` / `flag` Effect의 `flag` 필드를 실제 condition flag key로 처리하도록 수정했다.
기존 IR 호출에서 `key`가 없는 경우 flag 이름이 누락되는 문제를 제거했다.

## 테스트

- 신규 probabilistic migration 테스트: **2개**
- 전체 테스트: **349 passed**
- 이전 0.6.44: 347 passed
- 증가: **+2**
- 전체 회귀 실행 시간: **14.11s pytest time**

## 현재 의미

0.6.45는 단순 Rule registry 추가가 아니라 deterministic GimmickRegistry에 이어 **probabilistic branch/generated-action 경로에도 공통 Rule Runtime을 실제 연결한 버전**이다.

다음 단계는 실제 migration-safe Rule들을 identity/gimmick별 Golden Case로 고정하고, Legacy/IR 양쪽 결과의 state/damage/activation parity를 자동 검증하는 것이다.
