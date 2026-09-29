# Charge Count / Charge Potency Reference Audit — 2026-09-22 (finalized)

## 1. Catalog inventory

`identity_catalog_v2.json` / derived implementation backlog에서 `충전 위력`을 포함한 실제 원문을 전수 확인했다.

- 원문: 16건
- 고유 원문: 15건
- 관련 인격: identity-10116, identity-10410, identity-10713, identity-10913
- `충전`과 `충전 위력`은 별도 FighterState 필드로 유지된다.

## 2. 확인된 참조 유형

### 구현/연결 확인
- `충전 위력 N 이상 → 코인 위력 +X`
- `충전 위력만큼 합 위력 증가`
- `충전 위력 N 이상 → 코인 재사용`
- `충전 위력 N 이상 → 파괴 불가 코인`
- `충전 횟수 10 소모 → 충전 위력 1 획득` (명시적 Count→Potency Rule)
- `충전 횟수 10 소모 → 충전 1 획득`은 Potency를 올리지 않는 별도 Rule

### 아직 별도 Primitive가 필요한 유형
- `이 코인 최종 피해량의 (충전 위력 × 4/10)%만큼 참격 피해`
- `충전 역장을 (2 + 충전 위력)만큼 얻음`
- `충전 위력만큼 방어 레벨 증가`
- `충전 위력 × 5` / `충전 위력` 기반 보호막
- `속도 차이 × 충전 위력` 피해 증가
- `충전 위력 / 2` 기반 다음 턴 신속
- `충전 위력의 영향을 받지 않음`이라는 명시적 예외

특히 `최종 피해량의 ... 참격 피해`는 일반 `damage_percent`와 다른 **post-coin typed damage**다. 최종 코인 피해를 기준값으로 삼고 별도의 참격 피해로 처리해야 하므로 별도 Primitive가 필요하다.

## 3. '고유 충전' 확인

현재 catalog/backlog에서 literal `고유 충전`, `고유충전`, `unique_charge`를 별도 자원명으로 사용하는 항목은 확인되지 않았다.
따라서 존재하지 않는 별도 자원 축을 임의로 추가하지 않았다.

현재 프로젝트에서 별도 특수 자원으로 관리되는 이름이 확인될 경우 해당 자원 자체의 Rule/Contract를 기준으로 분리한다.

## 4. Count/Potency 계약

- Count → `fighter.charge`
- Potency → `fighter.charge_potency`
- 누적 명시적 소모 → `cumulative_resource_consumed[(identity_id), '충전']`
- Turn End Count -1은 누적 소모에 포함하지 않는다.
- Count가 0이 되어도 Potency는 자동으로 0이 되지 않는다.
- Potency는 명시적인 Rule이 있을 때만 증가한다.

## 5. 검증

현재 작업본에서 직접 실행한 결과:

- Charge/Resource 관련 targeted regression: **99 passed**
- Keyword Runtime targeted regression: **18 passed**
- E37 damage/golden 관련 selected regression: **48 passed**
- 전체 pytest: 120초 제한으로 마지막 구간까지 진행 후 종료되어 전체 pass로 판정하지 않음.
