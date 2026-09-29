# 림컴뎀계 0.5.5

## 이번 버전 핵심
- 사용자가 입력한 `actions`는 **Player Action 순서**로 유지한다.
- 패시브/스킬/흐트러짐으로 생긴 공격은 **Triggered Action**으로 실행 큐에 삽입한다.
- 실행 시점의 상태를 다시 확인하므로, 앞선 공격이 자원/상태를 바꾸면 뒤의 사용자 행동이 다른 스킬로 변형될 수 있다.
- `action_start_staggered`와 `action_end_staggered`를 분리하여 "공격 시작 전에는 흐트러지지 않음 → 공격 종료 시 흐트러짐" 조건을 구분한다.
- 생성 공격은 원래 사용자가 입력한 공명 순서를 새로 계산하지 않고, 자신의 스킬/자원 효과만 실행한다.
- 실행 결과에는 `requested_index`, `source_action_index`, `generated`, `state_at_action_start`를 기록한다.

## 현재 구조

`Scenario.actions`
→ `PlayerAction Queue`
→ `Resolve current state`
→ `Coin-by-coin execution`
→ `State Event`
→ `TriggeredAction insertion`
→ `next PlayerAction`

## 주의
자연어 패시브 전체를 완전하게 해석한 버전은 아니다. 이번 변경은 특히 보조공격/흐트러짐 파생/중간 자원 변화처럼 **행동 순서와 상태 전이가 중요한 계산 경로**를 일반화하는 단계다.
