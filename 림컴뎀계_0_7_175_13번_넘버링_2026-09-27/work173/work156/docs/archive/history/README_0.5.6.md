# 림컴뎀계 0.5.6

## 핵심 변경: 사용자 공격 순서와 런타임 파생 공격 분리

`actions`는 이제 명확하게 **사용자가 지정한 1차 공격 순서**다.

실행 중 패시브/스킬/흐트러짐/보조공격 등이 새로운 공격을 만들면 `ActionQueue`에 `TriggeredAction`으로 삽입한다.

### 실행 규칙

```text
사용자 지정 순서
  ↓
RequestedAction 1
  ↓
현재 상태에서 Skill Resolve
  ↓
코인별 실행
  ↓
상태 변화 / 흐트러짐 / Trigger
  ↓
TriggeredAction 즉시 실행
  ↓
TriggeredAction의 상태 변화 / 추가 Trigger
  ↓
다음 RequestedAction
  ↓
현재 상태에서 다시 Resolve
```

따라서 선행 행동으로 자원이 증가하면 뒤의 사용자 행동은 **실행 직전 현재 상태**를 기준으로 변형된다.

예: 새벽불 26 → 보조공격 → 새벽불 30 → 다음에 사용자가 입력한 그레고르 방어가 `새벽녘`으로 Resolve.

## 추적 정보

각 실행 결과에 다음을 기록한다.

- `requested_index`: 사용자가 지정한 원래 순서
- `execution_index`: 실제 실행 순서
- `generated`: 파생 공격 여부
- `source_action_index`: 어떤 요청에서 파생됐는지
- `source_event`: 어떤 Trigger가 만들었는지
- `trigger_chain`: 연쇄 파생 경로
- `depth`: 파생 깊이
- `state_at_action_start`: 행동 시작 시점 상태

## 안전장치

`max_trigger_depth` 기본값은 16이다. 파생 공격이 무한히 자기 자신을 생성하는 경우를 방지한다.

## 목표

이 구조는 새벽사무소에만 종속되지 않고, 이후 다음 종류를 같은 Action/Trigger 인터페이스로 확장하기 위한 기반이다.

- 보조공격
- 흐트러짐으로 발생하는 공격
- 특정 스킬 적중/종료 Trigger
- 자원 획득 후 스킬 변형
- Trigger가 또 다른 Trigger를 만드는 연쇄 효과
