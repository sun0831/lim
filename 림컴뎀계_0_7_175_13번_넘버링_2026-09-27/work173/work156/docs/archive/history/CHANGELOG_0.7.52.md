# 0.7.52 — newly_staggered 상태 전이 판정 정합화

## 반영
- `OneTurnSolverV29._fire_probabilistic_stagger_triggers()`의 `newly_staggered` 판정을 실제 상태 전이 기준으로 수정.
- 기존 구현은 `stagger_level` 증가 또는 `stagger_index` 증가만으로 새 Stagger를 판정했음.
- 이제 `before_staggered == false` → `after_staggered == true`인 경우에만 `newly_staggered`로 판정.
- 이미 Stagger 상태인 적이 Stagger Level을 증가시키거나, Level 3에서 threshold index만 증가하는 경우에는 신규 Stagger 트리거를 재발동하지 않음.
- `is_staggered`와 `newly_staggered`의 의미를 코드 경계에서도 분리.

## 검증
- `test_triggers_actions_queue.py` + `test_10409_jiji_exact.py`: **38 passed**
- 공격 종료 부정 효과 정신력 회복 / identity-specific / added-coin trace 관련 회귀: **37 passed**
- 별도 구조 테스트 `test_boundary_solver_structure.py`는 기존 catalog TriggerRule inventory 기대값 **67**과 현재 catalog 실제 **73**의 불일치로 1건 실패. 이번 변경과 무관한 stale assertion이며 수정하지 않음.

## 주의
- `newly_staggered`는 현재 Stagger 상태 여부가 아니라 **비-Stagger → Stagger 상태 전이**를 의미한다.
- 실제 인격 원문에서 요구하는 현재 Stagger 조건은 `is_staggered` 계열로 별도 처리한다.
