# E26 — status_effect_side_clause routing audit

- Removed the 149 `status_effect_side_clause` candidates from the Resource semantic scope by recording an explicit routing audit.
- 149 candidates / 129 unique clause texts were confirmed from the same E19 decomposition source.
- Routing is conservative: Buff/Debuff modifier, status effect, target/action compound, skill/classification, and generic status/effect routes are recorded.
- No new Status Runtime primitive was invented in E26.
- Existing `status_effect_catalog_v1.json`, `status_effect_lifecycle_v1.py`, `status_effect_runtime_v1.py`, and `buff_debuff_runtime_v1.py` remain the execution sources for already catalog-backed semantics.
- Identity-specific/compound semantics remain explicitly deferred rather than being falsely marked implemented.
- Added `STATUS_SIDE_CLAUSE_AUDIT_E26.json`, `.md`, and regression tests.
