# 0.5.78 — Unified analysis trace

## Changes
- Treat the unified goal as a stateful one-turn combat analysis engine.
- Expose `action_trace` as an explicit alias of the per-action trace for downstream analysis/UI.
- Expose a compact `state_diff` summary in solver output.
- Expose `next_turn_state` when present so Turn End preparation can be inspected without automatically simulating the next turn.
- Make the support-command regression test portable instead of depending on the old `/mnt/data/work063` extraction path.
- Preserve detailed per-identity, per-skill, per-coin and event-log data already produced by the runtime.
- Preserve the standard Bleed Clash assumption: when all Clashes are won, a 3-coin defender contributes Bleed procs as 3 + 2 + 1 = 6.

## Verification
- Full pytest suite verified on this package.
