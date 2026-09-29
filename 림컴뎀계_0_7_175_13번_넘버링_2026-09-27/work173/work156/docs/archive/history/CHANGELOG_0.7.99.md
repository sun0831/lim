# 0.7.99 — 버프/디버프 적용 주체 오판 수정

## 감사 목적
실제 버프/디버프 원문과 현재 계산기의 적용 주체(scope)를 대조하여, 이미 구현된 공통 Modifier가 잘못된 대상의 피해 계산에 섞이는 문제를 수정.

## 원문 근거
- `Protection`: 이 유닛이 받는 피해 감소
- `Fragile`: 이 유닛이 받는 피해 증가
- `Damage Up`: 이 유닛이 가하는 피해 증가
- `Damage Down`: 이 유닛이 가하는 피해 감소

## 확인된 오판
기존 `DamageModifierRuntime`은 공격자와 적 대상의 `BuffDebuffRuntime` modifier를 모두 동일한 `damage_percent` 채널로 합산했다.
그 결과:
- 공격자에게 `Protection`/`Fragile`이 있으면 공격자의 가하는 피해가 잘못 변동할 수 있음.
- 적에게 `Damage Up`/`Damage Down`이 있으면 적이 가하는 피해용 효과가 현재 공격자의 피해 계산에 잘못 유입될 수 있음.

## 수정
`BuffDebuffRuntime.resolve(..., scope=...)` 추가.
- `outgoing`: 공격자가 가하는 피해에 해당하는 효과만 취급
- `incoming`: 대상이 받는 피해에 해당하는 효과만 취급
- `all`: 기존 범용 호출 호환

`DamageModifierRuntime.resolve`는 피해 계산 시:
- 공격자 → `scope="outgoing"`
- 적 대상 → `scope="incoming"`

으로 분리.

## 테스트
- 관련 회귀: 148 PASS / 0 FAIL
- 추가된 핵심 테스트:
  - 공격자 Protection/Fragile 비적용
  - 적 Damage Up/Down 비적용
