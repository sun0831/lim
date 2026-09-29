# 0.6.47 — Catalog Rule Golden Migration Registry

## Objective
Move from hand-written golden examples to catalog-derived parity verification for every currently migration-safe TriggerRule.

## Implemented
- Added `test_v94_catalog_rule_golden_parity.py`.
- Builds the current 184-identity catalog and compiles the actual `GimmickRegistry`.
- Discovers all migration-safe emitted TriggerRules automatically.
- Executes Legacy and Rule IR paths against the same normalized scenario context.
- Verifies effect payload and activation parity for all discovered safe rules.
- Added `tools/build_migration_golden_registry.py`.
- Added generated `MIGRATION_GOLDEN_REGISTRY_0.6.47.json` containing the 20 verified migration-safe rules.

## Current migration boundary
- 55 emitted TriggerRules total.
- 20 migration-safe and golden-verified.
- 35 deferred to legacy/specialized execution.
- 0 unknown.
- Safe rules are consumed by `RuleMigrationRuntime.fire_migrated`; deferred rules remain on `TriggerRuntime`.

## Verification
- Catalog golden parity: 1 passed.
- Full regression: 356 passed.
- No legacy-rule deletion was performed without parity evidence.
