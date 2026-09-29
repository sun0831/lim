# 림컴뎀계 0.6.41 — 테스트 실행 계층화

## 이번 작업
- 테스트를 삭제하지 않고 개발 사이클별 실행 계층을 추가했다.
- `tools/test_suite_runner.py`가 기존 `TEST_INVENTORY_0.6.40.json`의 파일 분류를 이용해 관련 테스트만 선택한다.
- 전체 회귀는 기존 `pytest -q`로 그대로 유지된다.

## 검증
| Suite | 파일 | 결과 | 시간 |
|---|---:|---:|---:|
| smoke | 61 | 167 passed | 1.73s |
| runtime | 74 | 199 passed | 12.29s |
| integration | 75 | 203 passed | 6.41s |
| full regression | 전체 | 342 passed | 16.56s pytest |

## 해석
- 현재 테스트 342개를 삭제하거나 억지로 병합하지 않았다.
- 공통 Runtime 수정 시 smoke를 우선 실행할 수 있어, 매번 전체 342개를 돌리는 비용을 줄일 수 있다.
- Runtime 변경은 runtime, 기믹/통합 변경은 integration을 우선 실행한다.
- 패키지/릴리즈 전에는 반드시 full regression을 실행한다.

## 다음 병합 기준
테스트 간 입력/출력 계약이 동일하다는 것이 공통 Runtime의 Golden/Integration 검증으로 확인될 때만 레거시 중복 테스트를 병합한다.
