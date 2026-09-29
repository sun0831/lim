# 림컴뎀계 0.6.7

## Analyzer trace contract 강화
- Action별 `state_at_action_start`를 실제 행동 시작 전 상태로 고정.
- Action별 시작/종료 상태에 HP, Stagger, SP, 충전, 탄환, 호흡, 일반 자원, 상태이상 정보를 노출.
- Action별 `state_diff` 추가.
- Architecture audit이 Action-level state diff까지 계약으로 검증.
- 회귀 테스트 2개 추가.

## 검증
- 전체 테스트: 249 passed
- 0.6.6 대비 +2 테스트
