# 0.6.32 Architecture Foundations

## Added
- `target_runtime_v1.py`: Rule IR TargetIR -> deterministic target selection boundary.
  - self/ally/enemy/target candidate sources
  - alive/dead filtering
  - affiliation filtering
  - explicit target ids/index
  - delegates ranking/selection to existing `target_selector_v1`
  - no state mutation or target guessing
- `EffectRuntime` category normalization:
  - state
  - resource
  - status
  - modifier
  - action
  - legacy
- `RuleRuntime` now validates/resolves declarative targets before emitting EffectCommands.
- `RuleDependencyGraph.execution_order()` for deterministic dependency-safe rule work ordering.
- Tests for target resolution, effect categories, target failure behavior, and dependency ordering/cycle rejection.

## Compatibility
Existing TriggerRuntime/GimmickRuntime/DamageEngine remain authoritative for combat-state mutation. New architecture remains a migration boundary.

## Verification
- Python syntax check: PASS
- Full regression: **320 passed**
