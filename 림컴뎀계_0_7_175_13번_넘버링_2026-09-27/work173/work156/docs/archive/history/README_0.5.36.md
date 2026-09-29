# 림컴뎀계 0.5.36

## 이번 버전
### 확률형 Clash 내부 상태 전파 강화
- 각 Clash 교환 후 `after_clash` Trigger를 즉시 판정
- W/T/L 결과에 따른 SP 및 기존 상태 변경을 다음 Clash에 전달
- Trigger의 플래그/자원/상태 변경이 다음 Clash 확률 계산에 반영
- `queue_action`으로 발생한 추가 공격도 해당 확률 분기 안에서 실행
- 99 Clash 하드캡은 기존 규칙대로 유지
- 서로 다른 Trigger 상태가 같은 코인 결과를 만들 수 있는 경우 branch-local 상태를 보존
- `sp_set`, `sp_delta`, `enemy_sp_set`, `enemy_sp_delta` Trigger 효과 지원

즉, 이제 단순히 "한 번 계산한 W/T/L 확률을 끝까지 반복"하는 것이 아니라,
**Clash 1회 → 상태/Trigger 변경 → 변경된 상태로 다음 Clash 확률 재계산** 흐름을 만들었습니다.

## 검증
- `python run_tests.py`
- **82 passed**
- Python 문법 검사 통과

## 범위
현재 확률형 Clash의 핵심 상태 전파 축은 Bleed Count, HP/Stagger, SP, 자원, 상태/플래그 및 Trigger 연쇄입니다.
실제 게임의 모든 개별 인격 기믹이 자동으로 구조화된 것은 아니며, 구조화된 규칙이 존재하는 경우 우선 적용됩니다.
