# 7대 키워드 원문 → RuleIR → Runtime 추가 감사

기준: 2026-09-22 현재 `charge_audit2` 소스.

## 검증된 실행 경계

- Burn / Bleed / Tremor / Rupture / Sinking / Poise / Charge 공통 lifecycle runtime 존재.
- Charge Count와 Charge Potency는 별도 축이다.
- Charge Turn End -1은 cumulative spend에 포함되지 않는다.
- Charge Potency는 Count가 0이 되어도 유지된다.
- Sinking은 일반 SP 대상과 환상체/Non-SP 대상을 별도 경로로 처리한다.
- Sinking SP 초과분의 HP 전이는 `sinking_sp_overflow_to_hp` 명시 옵션일 때만 허용한다.
- Tremor Burst 기본 경로는 HP 피해가 아니라 Stagger Threshold 상승 + Count 소비다.
- Bleed의 Clash/Coin 확률 경로는 일반 KeywordRuntime과 별도 실행축을 유지한다.
- Poise Critical 소비는 logical coin당 1회 경계가 있다.

## 현재 회귀

- 집중 회귀: **126 passed**
- 빠른 전체 회귀 (`pytest -q -m 'not slow'`): **696 passed, 9 deselected**
- 전체 slow 9개는 별도 실행 범위이며, 이번 단계에서는 전체 705개 일괄 통과로 표기하지 않는다.

## 원문 기반 미연결/부분 연결 사례

현재 E35-7 coverage audit에서 키워드 문자열과 함께 잡히는 일부 Rule은 아직 RuleIR 실행까지 완결되지 않았다. 대표적으로 다음 유형이다.

1. **충전 역장**
   - 충전 최대치 초과분을 다음 턴 `충전 역장`으로 변환.
   - 현재는 일반 Charge Count/Potency와 혼합하지 않고 별도 특수 자원으로 남겨야 한다.

2. **충전 위력 기반 방어 레벨**
   - `충전 위력`에 비례한 방어 레벨 증가.
   - `충전 위력`을 `충전 횟수`로 읽으면 안 된다.

3. **충전 위력 기반 보호막**
   - 전투 시작/피격 직전 등 trigger가 서로 다른 보호막 효과.
   - 공통 ResourceRuntime과 TriggerRuntime을 통해 연결할 수 있지만 trigger별 Rule이 필요하다.

4. **충전 위력/충전 횟수 기반 피해량 증가**
   - `충전 x 3%`, `충전 x 5%` 같은 skill damage modifier는 기존 DamageModifier 계층을 사용한다.
   - 해당 수치를 일반 `charge_potency`로 대체해서는 안 된다.

5. **진동 폭발 추가 발동 확률**
   - `25% 확률로 1회 추가`는 일반 Tremor Burst와 별도의 probabilistic trigger다.

6. **턴 종료 다음 턴 피해량 증가**
   - 이번 턴의 실제 Burst 횟수를 다음 턴 상태로 넘기는 NextTurnState 경계가 필요하다.

7. **특수/무작위 상태 변환**
   - 여러 키워드 중 무작위 선택, 특정 조건에 따른 부여량 변환 등은 generic status lifecycle과 별도의 Rule/Effect가 필요하다.

## 원칙

- 위 사례를 `KeywordRuntime`에 인격별 if/else로 직접 박지 않는다.
- 공통 상태 저장은 Resource/Status Runtime이 담당한다.
- 발동 조건은 Rule/Trigger가 담당한다.
- 실제 수치 변화는 Effect/Modifier가 담당한다.
- 최종 피해 계산은 DamageEngine이 담당한다.
- 원문에 없는 효과를 추측하여 추가하지 않는다.

## 결론

이번 단계에서 **공통 7대 키워드 Runtime과 E37 피해 계산 경계는 회귀상 안정 상태**다. 남은 핵심은 키워드 자체의 기본 수식보다, 각 인격 원문에 존재하는 **trigger + target + resource transform + skill modifier + probabilistic trigger**를 RuleIR로 완전 연결하는 것이다.
