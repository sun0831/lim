# E28 Target Selection Audit

## Scope
- Source: `GIMMICK_GAP_REPORT_v4.md.json`
- Records tagged `target_selection`: 127
- Unique source texts: 126
- Clause count: 363

## Cluster counts
- `non_target_clause`: 117
- `multi_target_count`: 99
- `highest_resource_target`: 46
- `specific_identity_target`: 43
- `affiliation_target`: 42
- `lowest_resource_target`: 38
- `speed_target`: 38
- `unresolved_target_clause`: 30
- `random_target`: 26
- `hp_target`: 25
- `formation_target`: 20
- `target_relation`: 18
- `main_target`: 4
- `all_targets`: 3
- `status_target`: 0

## Primitive match counts
- `existing_target_selector`: 68
- `existing_resource_selector`: 84
- `existing_random_selector`: 26
- `existing_affiliation_resolver`: 42
- `existing_action_target`: 4
- `partial_common_primitives`: 295
- `new_primitive_candidate`: 0
- `unresolved`: 30

## Interpretation
Target selection is treated as a reusable selector axis, not a standalone identity runtime. Existing `target_selector_v1` covers speed, HP, random, and formation-edge selectors. Resource-aware lowest/highest selection is covered by the E20/E21 resource primitives. Affiliation is routed to the affiliation resolver. Remaining partial clusters are candidates for common selector/condition extensions, not identity-specific runtimes. Unresolved clauses are not claimed as implemented.
