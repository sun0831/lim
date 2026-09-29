# Charge Count / Charge Potency 의미 분리 검증

## 결론
- `충전 횟수(Charge Count)`와 `충전 위력(Charge Potency)`는 별도 상태축이다.
- Charge를 보유한다고 Potency가 자동으로 생성되거나 활성화되지 않는다.
- 턴 종료의 Charge Count -1은 실제 누적 소비(`cumulative_resource_consumed`)에 포함하지 않는다.
- Count가 0이 되어도 Potency는 별도 규칙에 의해 유지된다.
- 누적 Count 소비 → Potency 증가는 해당 효과를 명시한 인격의 Rule로만 실행한다.
- 누적 Count 소비 → Count 획득은 Potency와 별개의 Rule이다.

## 현재 카탈로그 확인
현재 `identity_catalog_v2.json`에서 `충전 횟수 10 소모 → 충전 위력 1`을 명시한 누적 Rule 소유자는 `identity-10116` 하나로 확인했다.

## Runtime 경계
```text
Charge Count
  ├─ gain
  ├─ explicit spend
  └─ turn-end decay (-1)

Charge Potency
  ├─ explicit Rule에 의한 gain
  └─ 일반 Charge Count 소비/턴 종료와 자동 연동하지 않음

Cumulative Charge Spent
  └─ explicit spend에서만 증가
```

## 테스트
`test_resource_runtime.py`, `test_resource_primitives.py`, `test_primitive_axis_regression.py`
- 94 passed
