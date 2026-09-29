# 0.7.30

- Reverted the incorrect generic `진동/파열 위력과 횟수 2배` implementation introduced in 0.7.29.
- Removed the generic RuleIR/compiler/runtime multiplier changes and their tests.
- From this version onward, Tremor/Rupture special effects are to be implemented from verified identity source entries only.
- The verified identity entry currently identified in `identity_catalog_v2.json` is `identity-10406` (LCCB 대리 료슈), skill `1040603` (대.박): `3코인 [크리티컬 적중 시] 진동, 파열 의 위력과 횟수가 2배로 부여됨`.
- No generic 2x multiplier rule is enabled by this release.
