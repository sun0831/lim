# 림컴뎀계 0.6.51 — Targeted Effect Migration

## 이번 사이클

`TargetResolver` 계열로 묶을 수 있는 deterministic targeted effects를 공통 EffectExecutor로 이관했다.

Migrated effects:
- `resource_gain_lowest_allies`
- `poise_gain_lowest_ally`
- `poise_gain_lowest_affiliation`
- `poise_gain_self_bonus`
- `heal_lowest_ally`

Selection/mutation 경계:
- Target selection: formation/affiliation/lowest metric semantics 유지
- Mutation: EffectExecutor
- Resource mutation: ResourceRuntime
- Affiliation membership/selection: AffiliationResolver
- Legacy special handler는 parity 확인 후 generic 실행 시 skip

## 추가 호환성 수정

`after_kill` migration path가 live `state`를 context에 전달하지 않아 generic targeted effect가 deferred되는 문제를 수정했다.
또한 generic migration context에 identity map fallback을 제공해 충전 대상 선정의 기존 `charge-capable` 우선순위를 보존했다.

## 결과

- TriggerRule: 55
- migration-safe rules: 47
- deferred rules: 8
- unknown rules: 0
- full regression: 367 passed
- test files: 132

남은 deferred effect는 `support_poise_count_bonus`, `hongmaehwa_crit`, `support_poise_gain`, `status/affiliation`, fatal prevention, highest-poise modifier, enemy-status count 등 특수 Runtime이 필요한 항목이다.
