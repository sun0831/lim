# 0.6.36 — Rule Migration Runtime

- Added `rule_migration_runtime_v1.py`.
- Legacy TriggerRule objects can be analyzed without semantic guessing.
- Fully generic effects are explicitly classified as migration-ready.
- Specialized action/affiliation/legacy effects remain deferred.
- Added opt-in `execute_generic()` so migration can proceed incrementally without changing existing combat behavior.
- Generated `RULE_MIGRATION_REPORT_0.6.36.json` from the 184-identity catalog.

## Verification

- Full regression: 332 passed.
- Syntax compilation: PASS.
