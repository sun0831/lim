# 0.6.18

- Added full per-identity keyword/affiliation/personal-mechanic matrix.
- Expanded combat affiliation module axis to the 16 confirmed modules from the 0.6.16 audit.
- Kept seven generic keywords independent from affiliation modules.
- Kept `생체 재료` on the Charge axis while Ring owns its lifecycle rules.
- Moved module ownership and concrete trigger builders for Ring, Middle, Spider House, Black Cloud, Pequod and Dawn Office into their module files.
- Added empty provider modules for confirmed affiliations without migrated concrete rule handlers yet.
- `special_gimmick_v2.py` now delegates module-owned trigger construction instead of containing the ownership map.
- Added regression tests for catalog coverage and module-local ownership.
- Full suite: 273 passed.

### 0.6.18-r1 — rule-layer physical split
- `gimmick_modules/common.py`: reusable cross-identity trigger shapes.
- `gimmick_modules/identity_specific.py`: identity-exclusive trigger rules.
- `special_gimmick_v2.py` no longer owns the large trigger execution switch; it dispatches parsed rules to module providers.
- `ModuleResolver.__deepcopy__` keeps imported provider modules shallow during probabilistic solver branching.
- Affiliation modules remain the owner for affiliation-specific mechanics; seven keyword modules remain independent.
