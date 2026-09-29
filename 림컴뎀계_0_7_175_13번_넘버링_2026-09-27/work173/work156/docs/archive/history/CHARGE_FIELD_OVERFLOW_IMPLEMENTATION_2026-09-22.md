# 충전 역장 / 충전 최대치 초과 런타임 경계 — 2026-09-22

## 이번 단계에서 실제 구현한 것

1. `ResourceRuntime.set()`이 최대치 초과 요청을 조용히 버리지 않고 `resource_overflow` 이벤트로 기록한다.
2. 이벤트에는 `resource`, `requested`, `maximum`, `overflow`, `before`, `after`, `reason`을 기록한다.
3. `충전 역장`은 `FighterState.charge`나 `charge_potency`와 합치지 않고 일반 독립 Resource 축으로 유지한다.
4. 기존 `충전 횟수` / `충전 위력` semantics는 변경하지 않았다.
5. 다음 단계의 실제 게임 규칙 연결은 이 이벤트를 소비하는 RuleRuntime 쪽에서 수행할 수 있게 경계를 만들었다.

## 확인된 실제 원문

`identity-10713 / W사 4등급 정리 요원 - CCA` 서포트 패시브에는 편성 첫 아군의 스킬이 충전 최대치를 초과해 충전 횟수를 얻은 경우 초과분을 다음 턴 `충전 역장`으로 전환하는 규칙이 존재한다. 최대 3이다.

동일 인격의 전투 패시브에는 충전 최대치 초과분에 따라 해당 스킬 피해량을 증가시키는 별도 규칙도 존재한다. 이 효과는 `충전 역장`과 별개의 규칙이다.

## 아직 연결하지 않은 것

- `resource_overflow` → 해당 초과 충전량을 실제 스킬/인격의 다음 턴 `충전 역장`으로 전환
- `충전 역장`을 실제 보호/피해 감소 등의 원문 효과에 연결
- 초과 충전량 → 해당 스킬 피해량 +3% 규칙의 실제 action-local 적용

위 세 가지는 원문이 서로 다른 소유자/타이밍을 가지므로 이번 단계에서 임의로 합치지 않았다.

## 테스트

`pytest -q test_charge_field_overflow_runtime.py test_charge_potency_final_damage_slash.py test_resource_runtime.py`

**39 passed**
