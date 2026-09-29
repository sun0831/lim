# 0.5.80 — generic damage-condition expansion

- Added dynamic status-sum / per-status damage scaling with optional caps.
- Added dynamic self named-resource-per damage scaling with optional caps.
- Added dynamic enemy current-HP threshold damage bonuses for `< / <=` and `> / >=` conditions.
- Fixed a latent `fighter` local reference bug in dynamic damage evaluation.
- Added regression coverage for the new parser/runtime paths.
- All tests pass: 162.

## Scope

These mechanics are evaluated from the current combat state at coin timing. Unsupported or ambiguous prose remains unsupported rather than being guessed.

## 0.5.81 — generic conditional coin-power coverage
- Extended conservative parser coverage for common conditional Coin Power rules:
  - main-target status potency/count thresholds
  - self status potency/count thresholds
  - self speed thresholds
  - self lost-HP percentage per Coin Power with caps
  - self + target status-sum Coin Power
  - target/main-target status-sum Coin Power
- Added runtime evaluation for new dynamic Coin Power conditions at coin timing.
- Added regression tests for parser/runtime behavior.
- Full test suite: 167 passed.
- Catalog audit: 621 attack skills, 1,980 supported clauses / 2,058 unsupported clauses (49.03% clause coverage under the current parser audit).
