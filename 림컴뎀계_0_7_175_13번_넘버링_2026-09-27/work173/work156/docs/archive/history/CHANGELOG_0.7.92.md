# 0.7.92 — 공통 버프/디버프 원문 정합성 감사 수정

## 목적
341KB 버프/디버프 원본 정의와 현재 공통 `status_effect_catalog_v1.json` / `StatusEffectRuntime`의 의미를 대조해, **구현은 존재하지만 원문과 다르게 해석된 공통 효과**를 수정.

## 확정 오판 1 — Base Power Up
원문:
- `Skill Base Power +X for this turn.`

기존:
- `base_power`를 `skill_power`로 매핑
- expiration도 `rule_or_source`

문제:
- Base Power와 Final Power가 합쳐질 수 있었음.
- 원문은 명시적으로 이번 턴 효과.

수정:
- semantic: `potency: base_power`
- modifier: `base_power_bonus`
- expiration: `turn_end`
- Damage Engine에서 `base_power_bonus`를 별도 합산

## 확정 오판 2 — Minus Coin Boost / Minus Coin Drop
원문:
- `Minus Coin Boost`: Minus Coin Power +X
- `Minus Coin Drop`: Minus Coin Power -X

기존 catalog:
- 둘의 positive/negative category가 반대로 되어 있음.

결과:
- Boost가 감소 방향으로 적용되고 Drop이 증가 방향으로 적용될 수 있는 구조.

수정:
- Minus Coin Boost → positive
- Minus Coin Drop → negative

## 별도 미구현 확인 — Multiply Coin Boost / Drop
원본에는 양쪽 효과 정의가 존재하지만 현재 공통 catalog에는 대응 항목이 없음.
이는 이번 작업에서 '오판'으로 카운트하지 않고 별도 미구현 gap으로 분리.

## 테스트
- `pytest -q test_status_effect_runtime.py test_damage_modifiers.py`
- 65 passed / 0 failed
