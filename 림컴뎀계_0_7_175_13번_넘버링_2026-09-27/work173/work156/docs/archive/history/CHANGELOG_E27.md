# E27 — Cross-Identity Semantic Audit

## Scope
- Source: `GIMMICK_GAP_REPORT_v4.md.json`
- Axis: `cross_identity`
- This is an analysis-axis audit, not a new identity-specific runtime.

## Source size
- Cross-identity-tagged records: 175
- Unique source texts: 173
- Clause candidates after conservative splitting: 503

> Note: an earlier project discussion cited 92 cross-identity records. The current full `GIMMICK_GAP_REPORT_v4.md.json` in the E26 artifact contains 175 records tagged with `cross_identity`. E27 uses the full current source rather than the earlier filtered subset.

## Semantic clusters
Counts overlap because one clause can contain multiple semantic components.
- affiliation_membership_count: 24
- cross_identity_event_trigger: 19
- cross_identity_target_selection: 113
- cross_identity_resource_effect: 92
- cross_identity_status_effect: 81
- cross_identity_skill_action: 27
- owner_participant_relation: 14
- formation_priority_selector: 5
- specific_identity_reference: 44
- non_cross_identity_clause: 168
- unresolved_cross_identity: 0

## Existing-runtime / primitive matching
- existing_affiliation_resolver: 23
- existing_target_selector: 111
- existing_trigger_runtime: 16
- existing_resource_runtime: 92
- existing_status_runtime: 80
- existing_action_runtime: 27
- partial_common_primitives: 238
- new_primitive_candidate: 0
- unresolved: 0

These are semantic-component matches, not full rule executability percentages.

## Main finding
No cross-identity-specific standalone primitive is justified by E27. The majority decomposes into existing Affiliation/Target/Trigger/Resource/Status/Action components. The remaining partial areas are:
- formation/slot priority selection
- explicit owner-vs-participant predicates
- specific identity/affiliation references
- composite ally-count conditions based on skill metadata

These should be resolved through common Condition/Target contracts rather than identity-specific modules.

## Tests
- E27 audit tests: 4 passed
- Cross-identity/affiliation regression set: 26 passed
- Full suite was attempted but did not complete within the execution window; it is not reported as a full-suite pass.
