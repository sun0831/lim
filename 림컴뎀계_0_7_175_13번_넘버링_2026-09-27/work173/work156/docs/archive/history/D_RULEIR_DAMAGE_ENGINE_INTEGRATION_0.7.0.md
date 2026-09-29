# D — RuleIR → DamageEngine 실행 연결 (2026-09-21)

## 목표
RuleIR의 generic damage modifier가 단순히 `EffectCommand`를 만드는 수준에서 끝나지 않고,
실제 `BattleState`의 canonical `DamageModifierRuntime` 상태를 변경한 뒤 `DamageEngine`의 coin timing에서 소비되는지 검증한다.

## 실행 경계

```text
TriggerRule / RuleIR
        ↓
ConditionRuntime
        ↓
RuleRuntime
        ↓
EffectRuntime → EffectCommand
        ↓
EffectExecutor
        ↓
DamageModifierRuntime (BattleState.runtime)
        ↓
DamageEngine.calculate_coin_damage()
```

새 Damage Runtime을 만들지 않는다. 기존 `DamageModifierRuntime`과 `DamageEngine`을 그대로 재사용한다.

## D에서 수정한 production 코드

`effect_executor_v1.py`

`EffectExecutor._modifier()`가 FighterState 객체에서 `id`를 찾던 기존 경로 때문에
RuleIR의 명시적인 `identity_id`/`target_identity_id`가 실제 modifier의 target bucket에 반영되지 않을 수 있었다.

수정 후 우선순위:

1. `target_identity_id`
2. `identity_id`
3. target 객체의 id/identity_id

source identity도 명시적인 `source_identity_id`와 event context를 우선 사용한다.

이 수정으로 다음과 같은 잘못된 상태:

```text
(target_identity_id="")
```

대신 실제 전투 인격 ID가 저장된다.

## 신규 테스트

`test_rule_ir_damage_connection_d.py`

3개 테스트:

1. RuleIR `damage_percent` → DamageModifierRuntime → 실제 DamageEngine 피해 증가
2. TriggerRule → RuleRuntime → 실제 coin damage 경로 연결
3. activation limit 1이 실제 modifier 등록과 함께 한 번만 적용되는지 검증

## 검증

Targeted:
- D integration + C boundary + effect/action: **21 passed**

Fast:
- **662 passed, 9 deselected**
- 3.18s

Slow:
- **9 passed, 662 deselected**
- 31.33s

전체 합계:
- **671 passed**

## 범위 제한

이번 D는 모든 RuleIR effect를 DamageEngine으로 직접 실행하도록 확장한 것이 아니다.
현재 generic damage modifier 계열이 실제 DamageEngine coin timing까지 연결되는 실행 경계를 고정한 것이다.

특수/미지원 effect는 기존 C 단계의 migration boundary 정책에 따라 deferred/전용 runtime 대상으로 남긴다.
