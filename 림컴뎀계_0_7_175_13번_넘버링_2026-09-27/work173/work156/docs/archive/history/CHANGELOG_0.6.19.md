# 0.6.19

- Expanded `combat_affiliations` from the previously migrated subset to all 16 affiliations marked `confirmed` by `AFFILIATION_AND_KEYWORD_AUDIT_0.6.16.json`.
- Updated `build_affiliation_taxonomy.py` so the confirmed set is reproducible instead of preserving only the legacy six-module subset.
- Updated `gimmick_module_registry_v1.py` fallback aliases for all 16 confirmed combat affiliations.
- Added regression coverage for manifest/taxonomy membership consistency and custom-identity fallback detection.
- Kept empty affiliation providers intentionally empty where concrete runtime rules have not yet been migrated; classification does not imply unsupported mechanics are implemented.
- Full suite: 280 passed.
