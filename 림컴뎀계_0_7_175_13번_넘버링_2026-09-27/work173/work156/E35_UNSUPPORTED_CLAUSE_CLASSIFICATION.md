# E35-3 Unsupported Clause Classification

- Unsupported clauses: **757**

| Classification | Count |
|---|---:|
| existing_primitive_parser_gap | 624 |
| data_or_parameter_gap | 78 |
| compound_clause_decomposition | 53 |
| true_runtime_gap | 2 |

## Interpretation
- `existing_primitive_parser_gap`: existing E34 primitives appear sufficient; parser/lowering is missing.
- `compound_clause_decomposition`: clause likely needs decomposition into multiple existing primitives.
- `data_or_parameter_gap`: semantic primitive exists but a required parameter/data contract is missing.
- `true_runtime_gap`: current primitive/runtime vocabulary does not safely represent the behavior.
- `unresolved`: insufficient evidence; do not guess.