# 0.7.54 — Stagger 강제 여부 Condition 경계 정합화

## 반영
- `ConditionRuntime`에 `stagger_forced` 조건을 추가.
- `ConditionRuntime`에 `newly_staggered_nonforced` 조건을 추가.
- `newly_staggered_nonforced`는 `비-Stagger → Stagger` 전이이면서 `stagger_forced == false`인 경우만 참.
- `stagger_forced`는 명시적으로 전달된 metadata만 사용하며 Stagger 수치 변화만으로 강제 여부를 추측하지 않음.
- 0.7.53의 `stagger_transition` metadata(`forced`)와 연결 가능한 공통 Condition 경계를 마련.
- 실제 인격의 강제 흐트러짐 규칙을 임의로 추가하지 않음.

## 검증
- `test_triggers_actions_queue.py` + `test_10409_jiji_exact.py`: **42 passed**

## 주의
- `newly_staggered_nonforced`는 새 Stagger 진입과 강제 여부를 동시에 검사한다.
- 기존 Stagger의 level/index 강화는 여전히 `newly_staggered`가 아니다.
