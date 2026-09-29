# 림컴뎀계 0.7.0

## 현재 버전
**0.7.0**

## 프로젝트 방향
1턴 지정 행동 순서 기반 피해 계산기. 사용자가 지정한 인격·스킬·행동 순서를 절대 기준으로 삼고, 해당 턴 안에서 발생하는 코인/클래시/상태/자원/패시브/원호공격/추가행동/기믹을 계산한다.

## 0.7.0 시작 기준
- 0.6.60의 Legacy Boundary 작업본을 기반으로 버전 승격.
- 확률/출혈 분기의 Production Legacy TriggerRuntime 직접 실행 경로 제거.
- `probabilistic_trigger_runtime_v1.py` 도입.
- 기존 0.6.x 문서는 역사 기록으로 보존.

## 다음 작업
- 남은 Production Legacy boundary 제거
- 테스트베드 정리
- 공통 Runtime 통합
- Action / Trigger / Support 안정화
- 출혈·파불코 확률 Runtime 심화
