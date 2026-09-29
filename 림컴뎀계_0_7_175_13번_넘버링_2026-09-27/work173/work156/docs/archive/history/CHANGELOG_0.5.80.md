# 0.5.80 — generic damage-condition expansion

- Added dynamic status-sum / per-status damage scaling with optional caps.
- Added dynamic self named-resource-per damage scaling with optional caps.
- Added dynamic enemy current-HP threshold damage bonuses for `< / <=` and `> / >=` conditions.
- Fixed a latent `fighter` local reference bug in dynamic damage evaluation.
- Added regression coverage for the new parser/runtime paths.
- All tests pass: 162.

## Scope

These mechanics are evaluated from the current combat state at coin timing. Unsupported or ambiguous prose remains unsupported rather than being guessed.
