# 림컴뎀계 0.5.17

## 이번 버전 핵심
특수자원 라이프사이클의 실행 범위를 확장했다.

### 지원 범위
- 스킬 사용시 특수자원 획득/고정 소비
- 조건부 특수자원 소비 (`X >= N`일 때만 소비)
- `최대 N까지 소모`
- `전부 소모`
- 코인 단위 특수자원 소비
- 코인 직전 자원값을 기준으로 소비하여 이후 코인에 최신 상태 반영
- 턴 시작시 특정 자원이 없을 때의 스킬 변형 패턴
- 기존 `획득 -> 임계값 -> 트리거 -> 추가 행동` 연쇄 유지

## 정확성 원칙
자동 추출된 특수자원 후보를 게임 규칙으로 무조건 승격하지 않는다.
애매한 자원명, 패시브 조건, 추가 효과는 검증 대상으로 남긴다.

## 검증
- `python run_tests.py`
- 36 passed
- Python 문법 검사 PASS

## 추가 산출물
- `SPECIAL_RESOURCE_EXECUTION_REPORT_v1.json`
- `SPECIAL_RESOURCE_EXECUTION_REPORT_v1.md`
- `test_v29_special_resource_lifecycle.py`
