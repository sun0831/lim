# 림컴뎀계 0.5.98 — 랜덤 타겟 수동 지정

## 변경 사항
- `target_override_ids` 추가.
- 스킬의 `target_policy: "random"`을 유지하면서 사용자가 실제 대상 ID를 강제로 지정할 수 있도록 지원.
- 우선순위: `target_override_ids` > `target_ids` > `target_policy` > 시나리오 기본값.
- 트리거/원호/강제 후속 행동으로 전달되는 타겟 메타데이터에도 override를 보존.
- 실행 로그에 `target_override_ids` 기록.
- 랜덤 타겟 수동 지정 및 다중 대상 순서 테스트 추가.

## 검증
- pytest: 215 passed
