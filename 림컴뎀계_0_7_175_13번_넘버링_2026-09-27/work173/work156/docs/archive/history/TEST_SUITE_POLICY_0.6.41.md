# 0.6.41 테스트 실행 계층 정책

## 목적
300개 이상의 테스트를 매 작업마다 모두 실행하는 시간을 줄이되, 테스트 자체를 삭제하지 않는다.

## 개발 사이클
- `python tools/test_suite_runner.py smoke` : Rule/Condition/Effect/Target/Runtime 핵심 변경 직후
- `python tools/test_suite_runner.py runtime` : 공통 Runtime 변경 후
- `python tools/test_suite_runner.py integration` : 기믹/인격 통합 변경 후
- `python tools/test_suite_runner.py all` : 릴리즈 전 전체 회귀

`all`은 기존 `pytest -q`와 동일하게 모든 `test_*.py`를 실행한다.

## 원칙
1. 테스트 삭제가 아니라 실행 계층 분리다.
2. 특정 작업과 무관한 테스트는 해당 작업 사이클에서 생략할 수 있다.
3. 최종 패키지 전에는 반드시 전체 Regression을 실행한다.
4. 병합은 공통 Runtime 이관으로 동일 계약이 중복 검증되는 것이 확인된 뒤에만 한다.
