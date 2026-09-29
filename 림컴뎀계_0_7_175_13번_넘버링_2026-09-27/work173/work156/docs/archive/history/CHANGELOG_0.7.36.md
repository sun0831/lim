# 0.7.36 — 재사용 적중시 진동 폭발 분리

## Source-backed target
- identity-10216 / skill 102162 `나비 베기`
- Source text:
  - `- 마지막 코인 재사용 (스킬당 최대 2회)`
  - `[재사용 적중시] 화상 1 부여`
  - `[재사용 적중시] 진동 폭발. 대상의 진동 횟수 1 감소 (스킬당 1회)`

## Implementation
- `[재사용 적중시]` effects are no longer treated as ordinary hit effects.
- They are attached to the logical last-coin reuse rule and execute on the reused logical coin.
- `reuse_index` is carried into coin effect context.
- Added `reuse_hit` condition type.
- The Tremor Burst Count reduction remains explicit: only this source clause carries `count_cost=1`.
- The Burn application has no implicit Count rule.
- The source's `스킬당 1회` limit is preserved on the Tremor Burst effect.

## Verification
- Targeted reuse/Burst/E35 tests: 37 passed.
- No generic Tremor Burst Count deduction was introduced.
- Other previously unresolved conditional burst patterns remain separate until their execution boundary is verified from source/runtime behavior.
