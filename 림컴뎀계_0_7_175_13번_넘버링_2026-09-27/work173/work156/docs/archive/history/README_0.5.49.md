# 림컴뎀계 0.5.49

## 이번 버전

### 적중 이벤트(after_hit) 공통화
- 실제로 피해를 준 코인 직후 `after_hit` Trigger를 실행한다.
- `after_hit`와 기존 `after_coin`을 분리한다.
  - `after_hit`: 실제 피해량 > 0인 코인에서만 실행
  - `after_coin`: 코인 종료 lifecycle 이벤트로 기존 동작 유지
- `after_hit`에서 발생한 상태/자원/플래그 변경과 추가 공격은 같은 branch의 다음 코인/행동에 반영된다.
- 확률형/생성 공격/Unopposed 코인 실행에서 동일한 적중 이벤트 경로를 사용한다.

### 조건 처리 보강
- 상태 Count/Potency 비교 조건을 TriggerRuntime에서 사용할 수 있도록 확장했다.
- 적/자신 HP 비율 조건도 TriggerRuntime 컨텍스트에서 평가할 수 있다.

## 검증
- pytest: 102 passed
- Python 문법 검사 통과
