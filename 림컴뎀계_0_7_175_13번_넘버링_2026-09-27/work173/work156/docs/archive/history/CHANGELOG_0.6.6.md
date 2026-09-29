# 0.6.6

## Analyzer Architecture Contract
- Action trace를 `Requested Action → Resolved Action → Triggered Action`으로 명시적으로 분리.
- 각 실행 action에 `action_type`, `requested_action`, `resolved_action`을 추가.
- 기존 damage/state/event trace는 유지하여 회귀 호환.
- `architecture_audit_v1.py` 추가: 결과 구조 계약 검사.
- `first_divergence()` 추가: 두 trace의 최초 차이 위치/필드 탐지.
- `ARCHITECTURE_SPEC_0.6.6.md`에 분석기 핵심 실행 계약을 문서화.
