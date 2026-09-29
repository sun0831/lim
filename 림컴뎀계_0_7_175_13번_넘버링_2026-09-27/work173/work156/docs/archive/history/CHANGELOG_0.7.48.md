# 0.7.48

## 약지 생체 재료 누적 소모 → 생체 재료 변환 공통화

- 실제 인격 원문 `소중한 작품 파시아(10215)` / `일생의 작품 티비아(10614)`의
  `전투 중 누적으로 자신의 생체 재료 횟수 10을 소모할 때마다 생체 재료를 1 얻음`
  규칙을 공통 `cumulative_resource_gain` Runtime으로 연결.
- 기존 누적 자원 변환 파서는 공백을 포함하는 자원명(`생체 재료`)을 처리하지 못했으므로,
  등록된 자원 vocabulary 기반으로 파싱하도록 확장.
- resource lifecycle의 threshold 재검사도 동일한 canonical resource vocabulary를 사용하도록 정렬.
- 10 단위 누적 소모마다 1회 변환되며, 한 이벤트에서 20/30을 초과해 여러 threshold를
  넘으면 교차한 횟수만큼 각각 발동하는 기존 semantics 유지.
- `생체 재료 위력 2 이상 → 작품명` 후속 조건은 별도 미구현으로 남겨 둠. 이번 변경에서
  해당 조건을 추측하여 추가하지 않음.

## 검증

- `test_identity_specific.py`
- `test_resource_runtime.py`
- `test_resource_primitives.py`
- `test_affiliation_modules.py`
- `test_rule_migration.py`
- 결과: **154 passed**
