# Engine Conversion Update — 0.7.0

## This pass
- Removed the second execution implementation inside `RuleRuntime.execute_legacy_rules`.
- Legacy-shaped TriggerRule objects are now converted to Rule IR and executed through the same `evaluate()` / `execute()` path used by common Runtime.
- Added activation reservation rollback when all concrete effects are deferred (for example `queue_action` without a live ActionQueue), preventing false activation consumption.
- Legacy `consume()` is retained only as compatibility accounting and is not part of effect execution.

## Validation
- Engine/migration/activation boundary suite: 17 PASS.
- Python compileall: PASS.
- Full suite was not claimed in this pass.

## Architectural result
Legacy TriggerRule is now an input format at this boundary, not a second execution engine. The remaining Legacy work is the specialized-effect parity queue and compatibility-only runtime cleanup.
