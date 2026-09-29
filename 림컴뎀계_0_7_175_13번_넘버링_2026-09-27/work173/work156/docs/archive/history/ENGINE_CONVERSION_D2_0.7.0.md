# Engine Conversion D-2 — Rule IR metadata / activation-cap preservation

## Scope
- Preserve migration metadata through `TriggerRule -> RuleIR` conversion.
- Enforce declarative turn-wide activation caps in the common `ActivationRuntime`.
- Normalize `received_target_id -> target_id` at the production event boundary so per-target activation uses the actual received target.

## Behavioral intent
This change does not introduce a new identity-specific runtime. It prevents activation semantics already present in the Rule record from being lost during migration.

## Verification
- Full suite: 430 passed.
- New contract tests: `test_v118_rule_ir_metadata.py` (2 tests).
- Existing Black Cloud/high-impact regression remains passing.
