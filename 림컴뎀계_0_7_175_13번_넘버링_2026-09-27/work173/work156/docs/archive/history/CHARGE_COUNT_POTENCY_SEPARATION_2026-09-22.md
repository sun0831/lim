# Charge Count / Potency 분리 — 2026-09-22

## 변경 목적

충전은 단일 정수 자원이 아니라 다음 두 축을 독립적으로 보유할 수 있도록 한다.

- `charge`: 충전 횟수(소모/획득되는 현재 수량)
- `charge_potency`: 충전 위력(충전 횟수와 독립적으로 유지되는 현재 위력)

누적 충전 횟수 소모량(`cumulative_resource_consumed`)도 별도 추적하며, 현재 충전 위력과 동일시하지 않는다.

## Runtime 계약

`ResourceRuntime`은 다음을 별도 리소스로 읽고 쓸 수 있다.

- `충전` -> `fighter.charge`
- `충전 위력` -> `fighter.charge_potency`
- `탄환` -> `fighter.ammo`
- `호흡` -> `fighter.poise.potency`

따라서 `충전`을 소비해도 `충전 위력`은 자동으로 감소하지 않는다.

## 입력

전투 시나리오에서 다음 입력을 지원한다.

```json
{
  "charge": 12,
  "charge_potency": 4
}
```

기존 입력의 `charge`는 그대로 동작하며, `charge_potency`가 없으면 0으로 초기화된다.
`charge_power`도 하위 호환 입력 별칭으로 허용한다.

## 출력

`fighters[id]`에 다음 두 값이 모두 노출된다.

```json
{
  "charge": 12,
  "charge_potency": 4
}
```

Action State Diff에도 `fighter_charge_potency_delta`가 추가됐다.

## 누적 소비량

`cumulative_resource_consumed[(identity_id, "충전")]`는 충전 횟수의 누적 소비량이다.
충전 위력은 이 카운터에 자동으로 연결하지 않는다.

예를 들어:

- 충전 20 → 10 소모
- 충전 위력 2 유지
- 누적 충전 소모량 10 기록

까지가 현재 공통 Runtime의 책임이다.

`"충전 횟수 10 소모할 때마다 충전 위력 1 얻음"` 같은 규칙은 이후 Rule/Gimmick 계층에서 이 누적 소비 이벤트를 받아 충전 위력을 증가시키도록 연결한다. 기존의 `충전 1 얻음` 규칙과 섞지 않는다.

## 호환성

확률 분기 상태 스냅샷 복원은 기존 Charge Potency 필드가 없는 10-tuple 형식도 읽을 수 있으며, 이 경우 Potency를 0으로 복원한다.

## 검증

- `test_resource_runtime.py` + `test_resource_primitives.py`: 59 passed
- 주요 Runtime/Engine/Identity/Trigger 회귀: 226 passed
- 전체 pytest: 120초 제한에서 완료 전에 중단됨. 전체 통과로 판정하지 않음.
