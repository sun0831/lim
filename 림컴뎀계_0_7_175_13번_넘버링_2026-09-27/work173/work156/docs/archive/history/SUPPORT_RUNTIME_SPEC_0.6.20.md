# Support Runtime Specification 0.6.20

## 목적

원호 공격/지원 공격/추격 공격에서 반복되는 "누가 공격하는가"와 "어떤 스킬을 사용하는가"의 해석을 하나의 범용 코드로 통합한다.

## 책임 분리

- TriggerRuntime: 발동 조건 판정
- SupportActionResolver: 지원 행동자/스킬 정책 해석
- GimmickRegistry: TriggerEffect를 GimmickAction으로 변환
- ActionQueue: 실제 행동 순서에 삽입
- DamageRuntime: 실제 피해 계산

## 예시

```text
[사용시] 우측 아군에게 원호 공격 명령
        ↓
TriggerRule
        ↓
support_action
  identity_policy=ally_right
  skill_policy=requested_next
        ↓
SupportActionResolver
        ↓
선택된 아군 + __support_default__
        ↓
ActionQueue
```

특정 인격의 이름을 런타임에 하드코딩하지 않는 것이 원칙이다.

## 향후 확장 후보

- `ally_by_condition`
- `lowest_resource_ally`
- `highest_status_ally`
- `same_affiliation_ally`
- `skill_policy=highest_requested_slot`
- 지원 공격의 대상 정책 별도 resolver
- 지원 공격의 횟수/턴 제한은 TriggerRuntime activation scope로 유지
