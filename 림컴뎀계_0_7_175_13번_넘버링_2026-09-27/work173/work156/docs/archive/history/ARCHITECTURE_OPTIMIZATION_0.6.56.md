# 림컴뎀계 0.6.56 — 확률 분기 Legacy Runtime 수명/Activation 최적화

## 목적

확률 분기에서 migration-safe Rule과 deferred compatibility Rule의 실행 경계를 명확히 유지하면서, deferred Legacy Runtime을 매 이벤트마다 재생성하던 비용과 activation 상태 손실을 제거한다.

## 변경

- `OneTurnSolverV29._fire_probabilistic_trigger_event()`에서 deferred `TriggerRuntime`을 branch-local runtime으로 유지.
- `state.runtime['probabilistic_deferred_trigger_runtime']`에 캐시하고 branch deepcopy 시 함께 복제되도록 구성.
- all-generic catalog 경로에서는 deferred Legacy Runtime을 생성하지 않음.
- declarative rule이 전혀 없는 runtime에 대해서만 기존 명시적 compatibility hook을 유지.
- 기존 migrated activation state(`probabilistic_trigger_activations`, buckets)와 deferred runtime activation을 서로 분리.

## 문제 해결

이전 구현은 deferred rule이 있을 때 이벤트마다 `TriggerRuntime(deferred)`를 새로 만들었다. 그 결과 `max_activations`, scoped activation bucket 등의 상태가 이벤트 사이에서 소실될 수 있었다.

현재는:

```text
Probability Branch
  ├─ Generic Rule → Rule IR → EffectExecutor
  └─ Deferred Rule → branch-local Legacy Runtime
                         ↓
                     activation 유지
```

## 검증

- 신규 테스트: 3개
- 전체 테스트: **380 passed**
- Python compile: PASS
- 기존 probabilistic migration / generated-action / legacy retirement 테스트: PASS

## 설계 원칙

Legacy Runtime은 생산 계산 경로의 기본 엔진이 아니라, 아직 Generic Runtime으로 표현되지 않은 명시적 compatibility boundary로만 존재한다.
