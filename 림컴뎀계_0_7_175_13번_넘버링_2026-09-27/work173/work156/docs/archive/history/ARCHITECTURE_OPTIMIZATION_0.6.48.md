# 0.6.48 Architecture Optimization

## Rule IR migration

- `resource_gain_affiliation_count` is now a common executable Effect.
- Affiliation membership is resolved through `AffiliationResolver` supplied in the Rule execution context.
- The effect remains owner-targeted and respects live/dead membership plus multiplier/cap.
- `GimmickRegistry._fire_migrated_event()` supplies the resolver to the common executor.
- Catalog migration-safe TriggerRules: **22 / 55**.
- Deferred TriggerRules: **33 / 55**.
- Unknown: **0**.

## Deferred inventory

Remaining deferred effects are predominantly action-queue/support effects and identity-specific state/poise/heal/fatal-prevention effects. They remain on the legacy/specialized path until an equivalent common runtime contract exists.

See `RULE_MIGRATION_REPORT_0.6.48.json` for the generated rule-by-rule inventory.

## Verification

- Focused migration tests: pass
- Full regression: **358 passed**
- Python syntax compilation: pass
