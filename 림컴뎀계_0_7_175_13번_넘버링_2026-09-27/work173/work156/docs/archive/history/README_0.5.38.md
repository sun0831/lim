# 림컴뎀계 0.5.38

## 이번 버전
### 확률형 Clash Trigger의 발동 횟수 상태 전파 보정
- 확률형 Clash의 각 W/T/L branch에서 `TriggerRuntime`의 `max_activations` 카운터를 branch state에 저장
- 다음 Clash로 넘어갈 때 이전 Clash에서 사용한 Trigger 발동 횟수를 복원
- 따라서 `max_activations: 1`인 Trigger가 Clash가 반복되는 동안 매번 다시 발동하는 문제 방지
- Trigger가 만든 상태/플래그와 함께 발동 횟수도 확률 branch의 상태축으로 취급
- terminal branch 및 이후 turn-level state propagation에서도 해당 상태를 유지
- 기존 `after_clash → 상태 변경 → 다음 Clash 확률 재계산`, coin-level unopposed trigger, 99 Clash hard cap, Bleed 5% 양 극단 제거 규칙 유지

## 검증
- `python run_tests.py`
- **84 passed**
- Python 문법 검사 통과

## 범위
실제 게임의 모든 인격 기믹이 자동 구조화된 것은 아니며, 현재는 구조화된 Trigger/자원/상태 규칙을 중심으로 확률 분기를 계산합니다.
