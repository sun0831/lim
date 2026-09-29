# 0.6.53 — Special-effect generic runtime completion

- Extended ConditionRuntime with `is_crit`.
- Moved `hongmaehwa_crit`, `enemy_status_count_gain`, `poise_gain`, `support_poise_gain`, and `support_poise_count_bonus` into generic EffectRuntime categories/executable registry.
- Implemented generic EffectExecutor handling for `hongmaehwa_crit`, `enemy_status_count_gain`, and `poise_gain`; existing support-poise handlers are now reachable through the generic path.
- Updated catalog Golden parity expectation and added `test_v100_special_effect_generic_runtime.py`.
- Verified full regression: 373 passed.
- Current catalog TriggerRules: 55 total, 55 migration-safe, 0 deferred, 0 unknown.
