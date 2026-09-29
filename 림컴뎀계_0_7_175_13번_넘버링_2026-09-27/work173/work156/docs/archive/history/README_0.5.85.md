# 림컴뎀계 0.5.85

0.5.85 is a verified incremental build of the one-turn stateful damage analysis engine.

### Verified
- 178 tests passed.
- ZIP root contains the project files directly.
- Explicit Tremor Burst / status trigger effects are modeled as stateful fixed-damage events.
- Explicit resource-consumption → Coin Power effects are modeled at skill-use timing.

### Audit
- 621 attack skills
- 2,205 supported parser clauses
- 1,833 unsupported parser clauses
- 54.61% parser-clause coverage

The audit counts parser clauses, not skills. Unsupported clauses include ambiguous, next-turn-only, targeting, multi-target, and special-mechanic prose that is intentionally not guessed.
