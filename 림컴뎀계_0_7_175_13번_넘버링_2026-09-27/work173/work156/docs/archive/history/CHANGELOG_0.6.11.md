# 0.6.11

## Module Loading / Keyword Classification

- Added `gimmick_module_registry_v1.py`.
- Added lazy module providers for the seven generic keywords and identity/faction gimmick groups.
- Added per-identity module manifests derived from catalog keywords, affiliations, resources and text.
- `생체 재료` is classified as **Charge-compatible** rather than as a new resource engine.
- Added module gates to selected Dawn Office, Middle, Pequod and Ring gimmick rules.
- Replaced the Captain Ishmael / Middle Finger parser checks with module-aware checks while preserving legacy behavior.
- Added `test_v66_module_loading.py`.
- Full suite: **257 passed**.
