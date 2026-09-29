# E27 Cross-Identity Audit

- Source records: 175
- Unique source texts: 173
- Clause candidates: 503

## Semantic cluster hits (overlap allowed)
- `non_cross_identity_clause`: 168
- `cross_identity_target_selection`: 113
- `cross_identity_resource_effect`: 92
- `cross_identity_status_effect`: 81
- `specific_identity_reference`: 44
- `cross_identity_skill_action`: 27
- `affiliation_membership_count`: 24
- `cross_identity_event_trigger`: 19
- `owner_participant_relation`: 14
- `formation_priority_selector`: 5
- `unresolved_cross_identity`: 0

## Primitive/runtime matching
- `partial_common_primitives`: 238
- `existing_target_selector`: 111
- `existing_resource_runtime`: 92
- `existing_status_runtime`: 80
- `existing_action_runtime`: 27
- `existing_affiliation_resolver`: 23
- `existing_trigger_runtime`: 16
- `new_primitive_candidate`: 0
- `unresolved`: 0

## Interpretation
- Cross-identity is treated as an analysis axis, not a standalone runtime.
- Affiliation membership/count is already backed by `AffiliationResolver`; target/event/resource/status/action components should be composed with common runtimes.
- Formation-order, owner/participant, and explicit identity-reference predicates remain partial until a common Condition/Selector contract is finalized.
- Do not treat clause counts as executable coverage; a single clause can contain several semantic primitives.
