# Charge / Charge Potency Identity Audit — 2026-09-22

## 결론

`충전` 키워드를 보유한 모든 인격이 `충전 위력`을 얻는 구조가 아니다.

현재 `identity_catalog_v2.json`의 충전 보유 인격 25개를 검사한 결과:

- `충전 위력`을 명시적으로 생성하는 누적 소모 Rule: **1개**
  - `identity-10116` — LCE E.G.O::차원찢개 이상
  - 원문: `전투 중 누적으로 자신의 충전 횟수 10 소모할 때마다 충전 위력 1 얻음`
- `충전 위력`이라는 값을 참조하지만 생성하지 않는 인격:
  - `identity-10713` — W사 4등급 정리 요원 - CCA
  - `identity-10410` — 로보토미 E.G.O:: 적안・참회 (오히려 충전 위력의 영향을 받지 않는다고 명시)
  - `identity-10913` — 로보토미 E.G.O:: 눈물로 벼려낸 검 (깊은 눈물이 충전 위력의 영향을 받지 않는다고 명시)
- 여러 인격의 `전투 중 누적 충전 횟수 10 소모` Rule은 목적지가 `충전`이며, `충전 위력` 증가가 아니다.

## 구현 원칙

1. Charge 보유 여부만으로 Charge Potency 시스템을 활성화하지 않는다.
2. `charge_potency`는 독립 상태값으로 유지한다.
3. 누적 Charge 소비 이벤트는 모든 Charge 인격에서 기록할 수 있지만, 실제 Potency 증가는 해당 인격에 명시된 Rule이 있을 때만 실행한다.
4. 턴 종료 Count 감소는 누적 소비 이벤트가 아니다.
5. Count가 0이 되어도 Potency는 자동 감소하지 않는다.
6. `충전 10 소모 → 충전 1 획득`과 `충전 10 소모 → 충전 위력 1 획득`은 서로 다른 Rule이다.

## 회귀 보호

- `test_resource_runtime.py`: **34 passed**
- 새 검증:
  - 카탈로그의 명시적 Charge Potency 생성 Rule 소유자가 `identity-10116` 하나인지 확인
  - 대표적인 비-Potency Charge 인격들의 누적 Charge 소비가 `charge_potency`를 변경하지 않는지 확인
