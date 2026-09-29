# 0.5.87 — flat additional coin damage

- Added conservative parsing for coin-local flat additional damage patterns such as `1코인 [앞면 적중시] 추가 피해 +3`.
- Flat additional damage is represented as a post-hit `damage_fixed` effect, so it is not confused with percentage damage modifiers.
- `[앞면 적중시]` / `[뒷면 적중시]` remain face-specific; `[적중시]` applies on hit.
- Added regression tests for parser placement and flat-vs-percent semantics.
- Full test suite: 183 passed.
