# 림컴뎀계 Analyzer Architecture Contract 0.6.6

## 목적
1턴의 사용자가 지정한 입력과 행동을 실제 전투 메커니즘 순서로 재현하는 분석기다. 자동 플레이/최대 딜 탐색은 핵심 범위가 아니다.

## 실행 단계
`INPUT/START_STATE → REQUESTED ACTION → RESOLVED ACTION → COIN/STATE MUTATION → TRIGGERED ACTION → TURN END → NEXT_TURN_STATE`

### Action 분리
- **Requested Action**: 사용자가 입력한 행동. 순서와 의도는 보존한다.
- **Resolved Action**: 변환/조건 판정 후 실제 실행된 인격·스킬.
- **Triggered Action**: 원호/추가/강제/후속 행동. source action/event/trigger chain을 보존한다.

### 상태 추적
코인 처리 직후 HP, SP, Stagger, 자원, 버프/디버프, Potency/Count를 갱신한다. 후속 코인은 갱신된 상태를 사용한다.

### 결과 계약
Result는 최소한 다음을 노출한다.
- requested_plan / actions
- damage_by_identity / damage_by_skill
- event_log
- state_diff
- next_turn_state

각 action은 action_type, requested_action, resolved_action, coin trace, action 시작/종료 상태를 가진다.

### 검증
`architecture_audit_v1.py`는 위 계약을 구조적으로 검사하며, `first_divergence()`는 두 trace 사이의 최초 차이 index/field를 반환한다.

## 범위 밖
자동 다중 턴 플레이, 전역 최대 딜 탐색, 불명확한 텍스트 효과의 임의 추정.
