# 림컴뎀계 0.7.0

## 버전업

기존 0.6.60 계열 작업본을 기준으로 프로젝트 버전을 **0.7.0**으로 승격한다.

### 7번 작업 반영
- Legacy Event Boundary 분리 작업 반영
- 확률/출혈 분기에서 Production의 Legacy TriggerRuntime 직접 실행 경로 제거
- `probabilistic_trigger_runtime_v1.py` 도입
- 확률 branch의 activation scope/counter 상태 유지
- Legacy boundary 회귀 테스트 반영

### 검증 기준
- 변경 전후 기존 기능을 유지하는 것을 우선한다.
- 0.6.60의 역사적 문서는 변경하지 않고 보존한다.
- 0.7.0부터 신규 작업/변경 기록을 이 버전 기준으로 누적한다.

### 0.7.0 다음 작업
1. 남은 Production Legacy boundary 조사/제거
2. 테스트베드 정리
3. 공통 Runtime 통합
4. Action / Trigger / Support 안정화
5. 출혈·파불코 포함 확률 Runtime 심화
