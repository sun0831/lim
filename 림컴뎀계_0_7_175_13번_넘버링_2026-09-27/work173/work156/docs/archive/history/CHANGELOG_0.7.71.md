# 0.7.71 — 실제 원문 오판 감사 2차 수정

## 목적
구현율을 세는 작업이 아니라, 실제 인격/스킬 원문과 계산기 내부의 기믹 해석이 달라지는 오판을 찾고 수정.

## 이번에 발견·수정한 오판

### 1. AllySelectorTarget의 `hp_min` / `hp_max`
- 원문 의미: `체력이 가장 낮은/높은`은 현재 HP 절대값 비교.
- 기존 `AllySelectorTarget`에는 `hp_min`/`hp_max`의 명시적인 값 처리가 없어 generic fallback으로 들어가 모두 같은 값(0)처럼 취급될 수 있었음.
- 수정: 현재 HP 절대값을 비교하도록 명시.
- `hp_percent_min/max`와 `max_hp_min/max`는 기존 의미를 유지.

### 2. 상태 보유자 + 정신력 최저 Selector
- 정책: `status_present_sp_min:<상태>` / `status_present_sp_max:<상태>`.
- 기존에는 상태 필터 후 SP 정렬을 수행했지만 이후 generic 정렬 단계가 다시 실행되어 SP 순서를 잃을 수 있었음.
- 수정: 해당 복합 Selector는 필터 → SP 정렬 → 즉시 결과 반환.

## 검증
- `test_ow_0_7_71_semantic_mismatch.py`
- `test_target_selection.py`
- `test_identity_specific.py`
- `test_triggers_actions_queue.py`
- 결과: 114 passed / 0 failed

## 주의
이번 수정은 실제 원문과 의미가 다른 오판만 대상으로 한다. 단순 미구현 기믹은 이번 오판 카운트에 포함하지 않는다.
