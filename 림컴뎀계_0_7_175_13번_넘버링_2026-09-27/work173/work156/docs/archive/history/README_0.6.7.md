# 림컴뎀계 0.6.7

0.6.7은 Analyzer Architecture의 추적성을 강화한 패치입니다.

각 실행 Action은 `Requested Action → Resolved Action → Coin Trace → State Mutation` 흐름을 보존하며, 행동 시작 전과 종료 후의 전투 상태 및 상태 차이를 함께 제공합니다.

주요 추가 필드:
- `state_at_action_start`
- `state_at_action_end`
- `state_diff`
- actor/target 상태이상 및 자원 snapshot

전체 테스트 249개 통과.
