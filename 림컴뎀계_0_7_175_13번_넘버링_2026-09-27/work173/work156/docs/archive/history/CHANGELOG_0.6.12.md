# 0.6.12

## Keyword / Affiliation axis separation

- Separated the seven generic combat keywords from identity/faction-specific gimmick affiliations at the manifest level.
- Added explicit `keyword_modules` and `affiliation_modules` views while preserving the backward-compatible `modules` union.
- Module summary now reports active generic keyword modules and active affiliation modules independently.
- Ring Finger `생체 재료` remains mapped to the generic `Charge` keyword; Ring/Spider House remain affiliation modules.
- Added regression tests for overlapping keyword + affiliation classifications.

Tests: 259 passed.
