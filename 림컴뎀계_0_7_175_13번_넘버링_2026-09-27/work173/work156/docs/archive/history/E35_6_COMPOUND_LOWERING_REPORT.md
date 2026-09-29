# E35-6 Compound Clause Lowering

## Scope
Conservative lowering of E35-5 compound clauses into existing RuleIR vocabulary. No new Runtime family is introduced.

## Input
- E35-5 unsupported/compound rows: 808

## Audit
- implemented: 2
- partial: 80
- no safe lowering: 726

`partial` means at least one known RuleIR node was extracted while one or more fragments remain unknown. It is not counted as fully executable coverage.

## Safety rules
- Unknown fragments are retained in metadata.
- No arbitrary semantics are inferred from opaque Korean prose.
- Existing Primitive contracts are reused.
- Compound lowering is separate from the legacy parser and does not remove the legacy bridge.
