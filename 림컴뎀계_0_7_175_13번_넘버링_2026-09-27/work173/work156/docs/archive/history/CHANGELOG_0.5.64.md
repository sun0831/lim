# 0.5.64 — Forced / self follow-up action layer

- Added conservative parsing for deterministic self-triggered follow-up skills of the form `기본 공격 스킬 종료 시 자신의 X N 이상이면, 'Y' 발동`.
- Generated actions can now target the same identity as the triggering action; the previous blanket self-target rejection was removed.
- Added `resource_gte` trigger condition for explicit fighter-resource thresholds.
- Preserved conservative behavior: ambiguous received-hit triggers and unspecified ally/enemy target selection are not auto-executed.
- Added regression tests for self-follow-up execution metadata and conservative rejection.

Verification: 128 pytest tests passed.
