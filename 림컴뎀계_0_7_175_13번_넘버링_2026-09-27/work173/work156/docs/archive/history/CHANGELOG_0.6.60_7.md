# 림컴뎀계 0.6.60 — 7번 작업 기록

## Legacy Boundary / Probability Runtime

- 확률(출혈) 분기에서 `TriggerRuntime` 직접 실행 경로 제거.
- `probabilistic_trigger_runtime_v1.py` 추가.
- 확률 분기의 generic effect는 기존 Rule IR/공통 Runtime 경로를 사용.
- deferred/specialized effect는 branch-local 확률 Runtime에서 activation 상태를 유지하면서 이벤트 payload로 전달.
- 확률 분기 deepcopy 이후에도 activation scope/counter가 유지되도록 기존 state synchronization과 연동.
- 생성 공격 테스트의 branch-local runtime monkeypatch 계약 유지.
- Legacy boundary 회귀 테스트 추가.

## 검증

- 관련 Legacy/확률 테스트: 24 PASS
- 변경 후 전체 테스트: **392 PASS**
- `one_turn_solver_v29.py`의 `TriggerRuntime` 직접 생성/호출 경로: 제거
- Production의 `legacy_event_compat_v1` 직접 import: 0건

## 다음 단계

1. 남은 Production Legacy boundary 조사
2. 테스트베드 중복/구형 테스트 정리
3. 공통 Runtime 통합
4. Action / Trigger / Support 안정화
5. 출혈·파불코 포함 확률 Runtime 심화
