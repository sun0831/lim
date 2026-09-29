# 0.5.82 — generic status/clash condition coverage

- Extended skill-text parsing for self status-count gains at skill use, e.g. `자신의 진동 횟수 2 증가`.
- Extended Clash Win/Lose parsing for numeric status-count changes, e.g. `[합 승리시] 파열 횟수 2 부여`, using the existing `SkillData.effects_on_clash_win/lose` lifecycle.
- Added exact speed-difference coin-power condition parsing, including both directions.
- Added regression tests for all three patterns.
- Full test suite: 170 passed.
- Parser audit after this change: 2,063 supported / 1,975 unsupported clauses across 621 attack skills (51.09% clause coverage under the current parser audit).
- Audit remains a parser-clause metric, not a direct measure of end-to-end skill damage accuracy.
- Intentionally left ambiguous effects such as generic Tremor Burst, AoE targeting, random target selection, and complex resource conversions unsupported rather than guessing their semantics.
