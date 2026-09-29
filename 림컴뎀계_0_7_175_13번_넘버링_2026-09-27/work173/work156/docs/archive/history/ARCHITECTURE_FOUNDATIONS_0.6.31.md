# 0.6.31 Architecture Foundations

## Added
- `condition_runtime_v1.py`: common Rule IR condition evaluator, independent of legacy TriggerCondition.
- `effect_runtime_v1.py`: side-effect-safe Effect IR command/handler dispatcher.
- `rule_runtime_v1.py`: common Rule IR evaluation shell; evaluates conditions and emits EffectCommands without mutating battle state.
- `test_v79_condition_effect_ir.py`
- `test_v80_rule_runtime.py`

## Compatibility principle
Existing TriggerRuntime/GimmickRuntime/DamageEngine remain authoritative for battle-state mutation. The new layer is a migration boundary, not a rewrite.

## Verification
- Python syntax check: PASS
- Full regression: 314 passed
