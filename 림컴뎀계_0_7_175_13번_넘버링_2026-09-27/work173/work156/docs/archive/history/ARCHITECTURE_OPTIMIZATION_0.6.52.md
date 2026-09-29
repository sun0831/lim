# 림컴뎀계 0.6.52 — generic special-effect executor

## 목적
Rule IR migration의 남은 공통 state/status effect를 실제 EffectExecutor에서 실행 가능하게 만들어 Legacy 의존도를 줄인다.

## 변경
- `support_poise_gain` → 공통 EffectExecutor
- `support_poise_count_bonus` → 공통 EffectExecutor
- `register_fatal_prevention` → 공통 state effect
- `register_damage_modifier_highest_poise` → AffiliationResolver + DamageModifierRuntime
- `status_gain_affiliation` → AffiliationResolver + Status mutation
- Golden parity context에 affiliation resolver를 제공해 battle-start affiliation rule의 activation parity 검증
- generic special-effect regression tests 추가

## 검증
- 전체 회귀: 371 passed
- catalog TriggerRule: 55
- migration-safe: runtime 분석 결과 참조
- unknown: 0
