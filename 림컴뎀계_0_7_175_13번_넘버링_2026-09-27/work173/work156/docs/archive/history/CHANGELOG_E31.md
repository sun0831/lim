# E31 — Multi-Target Audit

## Scope
Audit the `multi_target` axis against the current shared Target/Action primitives.

## Result
- Records tagged `multi_target`: 35
- Unique source texts: 34
- Clause count: 152
- New dedicated multi-target primitive/runtime: **0**

## Routing
- Explicit target counts → existing target-count / `target_count` contract
- All-target selection → existing target selector + count composition
- Random N targets → existing random selector + count
- Conditional N targets → Condition + Target Selector composition
- Focused-battle `부위` routing → target resolution
- Single-target clauses → existing Action Target handling

## Tests
- E31 audit tests: **4 passed**
- Full regression collection: to be measured; no full-suite PASS claim unless execution completes.
