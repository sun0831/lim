# 0.5.63

## Implemented
- Extended `ActionRequest` / `ActionQueue` with explicit target-selection metadata.
- Added deterministic target selector primitives for fastest/slowest, HP max/min, HP-percent max/min, formation order, and explicit target IDs/indexes.
- Action execution trace now exposes requested target policy/index/IDs and resolved target selection when per-target enemy data is supplied.
- Trigger-generated actions inherit trigger metadata through the queue model.

## Compatibility
- Existing aggregate `enemy` state remains the default.
- Random target selection is not guessed; it requires an explicit resolved choice/seed at the caller layer.
- Existing 0.5.62 tests remain green.
