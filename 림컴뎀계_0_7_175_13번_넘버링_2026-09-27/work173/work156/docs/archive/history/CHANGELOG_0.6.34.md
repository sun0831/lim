# 0.6.34

- Added `effect_executor_v1.py` as the concrete mutation boundary for generic Rule IR effects.
- Added `RuleRuntime.execute()` for evaluate → execute flow.
- Reused ResourceRuntime and DamageModifierRuntime instead of duplicating mutation logic.
- Kept support/assist/extra/legacy effects deferred to specialized runtimes.
- Added 3 executor tests.
- Full regression: 327 passed.
