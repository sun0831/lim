# RuleIR 실행 경계 SPEC — 0.7.0

## 목적

A3/A4에서 activation state를 `ActivationLedger` 하나로 통일한 다음,
RuleIR이 실제 전투 Runtime으로 들어가는 경계를 고정한다.

이 문서는 **게임 규칙의 증명**이 아니라 현재 프로젝트의 실행 계약(SPEC)이다.
실제 게임 일치 여부는 별도의 Golden에서 검증한다.

## 1. 상태 소유권

```text
RuleIR / TriggerRule definition
        ↓
ActivationLedger
        ↓
RuleRuntime / specialized Runtime / Solver
```

- RuleIR/TriggerRule은 규칙 정의만 가진다.
- mutable activation count/bucket은 `ActivationLedger`가 소유한다.
- `ActivationRuntime`은 Ledger에 위임한다.
- Solver가 Rule definition에 activation state를 다시 기록하지 않는다.

## 2. 실행 경계

### Production

```text
input event
  → RuleMigrationRuntime.production_fire
  → migration-safe RuleIR
  → RuleRuntime
  → ConditionRuntime
  → TargetRuntime
  → EffectRuntime
  → EffectExecutor / ActionQueue
```

production 경로에서는 migration-safe rule을 `TriggerRuntime`으로 되돌리지 않는다.
지원되지 않는/deferred rule이 production 경계에 들어오면 fail-fast한다.

### Temporary parallel audit

```text
same input
  ├→ Legacy TriggerRuntime
  └→ RuleIR → RuleRuntime
          ↓
       normalized result compare
```

이 경로는 검증용이다. production 실행 경로가 아니다.

비교 대상은 최소한:

- fired rule identity
- effect payload
- activation total count
- activation buckets

이어야 한다.

Parallel audit가 통과했다고 해서 실제 게임 규칙과 일치한다고 간주하지 않는다.

## 3. Migration safety

RuleIR 변환에서 정확히 표현되지 않는 clause/effect는 추측으로 실행 가능한 것으로 만들지 않는다.

- generic + supported condition → migration-safe
- specialized/deferred/unknown → migration boundary 밖
- production에서 deferred rule 발견 → `RuntimeError`

## 4. activation 계약

`turn_cap`은 Rule metadata에 존재할 수 있지만 Ledger가 metadata를 임의로 읽는 것이 아니라
호출자가 명시적으로 전달한다.

현재 공통 Runtime은 다음 의미를 사용한다.

```text
ActivationRuntime
  → rule.metadata.turn_cap
  → ActivationLedger.eligible(..., turn_cap=...)
```

## 5. 범위 제한

현재 C 단계는 **RuleIR 실행 경계 확립**까지다.

다음 항목은 후속 단계다.

- 전체 RuleIR catalog coverage 확대
- specialized gimmick의 실제 IR execution migration
- Damage Engine과의 완전한 연결
- 실제 게임 Golden
- Legacy Runtime 제거

## 6. 완료 기준

C 단계에서 다음을 만족해야 한다.

1. production generic rule은 RuleRuntime 경로만 사용한다.
2. production event boundary에서 Legacy fallback이 발생하지 않는다.
3. deferred rule은 fail-fast한다.
4. parallel audit은 Legacy와 RuleIR 결과를 별도 상태에서 비교한다.
5. activation parity는 Ledger 기준으로 비교한다.
6. RuleIR conversion coverage와 gameplay execution coverage를 같은 수치로 취급하지 않는다.
