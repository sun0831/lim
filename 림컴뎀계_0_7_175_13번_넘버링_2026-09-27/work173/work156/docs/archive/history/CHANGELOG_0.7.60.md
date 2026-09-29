# 0.7.60 — 편성 순서 Target Selector 정합화

## 범위
실제 인격 데이터에서 반복 확인되는 `편성 순서가 가장 빠른/느린 아군` 대상 선택을 기존 formation selector로 통합했다.

## 변경
- `target_selector_v1.py`
  - `fastest_formation_ally` → `formation_min`
  - `slowest_formation_ally` → `formation_max`
  - `earliest_ally` → `formation_min`
  - `latest_ally` → `formation_max`
- `passive_runtime_v29_base.py`
  - `AllySelectorTarget`이 `formation_min/max`를 직접 평가하도록 확장.
  - `FighterState.formation_index`가 있으면 이를 사용하고, 없으면 기존 fighter 순서를 fallback으로 사용.
- 새 Runtime/새 상태 필드는 만들지 않음.

## 해석 경계
- `편성 순서가 가장 빠른 아군`은 속도가 아니라 편성 위치가 가장 앞선 아군으로 처리한다.
- `속도가 가장 빠른 아군`과는 별도 selector다.
- `편성 순서 1번인 아군`처럼 특정 슬롯을 지칭하는 문구는 이번 변경에서 일반화하지 않았다.

## 검증
- `test_target_selection.py`
- `test_identity_specific.py`
- `test_triggers_actions_queue.py`
- 결과: **104 PASS / 0 FAIL**

## 주의
실제 특정 인격의 전체 효과가 자동 실행된다는 의미가 아니다. 이번 변경은 반복되는 편성 순서 대상 선택 primitive의 재사용 경계를 정합화한 것이다.
