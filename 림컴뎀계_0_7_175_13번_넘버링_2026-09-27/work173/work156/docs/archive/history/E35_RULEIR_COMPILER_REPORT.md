# E35-1 — Clause → RuleIR Compiler

## Scope

This pass adds the first canonical compiler boundary from the existing v29 prose
clause compiler to the shared RuleIR. It does not replace the legacy runtime and
does not introduce a new execution runtime.

## Pipeline

`clause text -> passive_compiler_v29 -> PassiveDefinition -> RuleIR`

The lowering is loss-aware. Condition/effect objects are structurally serialized,
and each lowered condition/effect carries the E34 primitive contract ID used for
routing. Source text and deferred-turn information are retained in RuleIR.

## Validation

- E35 focused tests: 46 passed.
- E35 + E34 registry + E17-E33 primitive regression + RuleIR foundation/migration/
  legacy-boundary tests: 122 passed.
- No failures in the focused scope.

## Deliberate non-goals

- No Legacy deletion.
- No new Runtime class.
- No claim that all catalog clauses are executable.
- Unsupported clauses remain unsupported rather than being fabricated into RuleIR.
- Full 571-test regression is deferred to the appropriate integration checkpoint.
