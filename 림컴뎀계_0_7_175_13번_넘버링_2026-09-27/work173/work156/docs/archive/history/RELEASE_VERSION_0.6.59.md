# 림컴뎀계 0.6.59

## 이번 버전
- Legacy event compatibility separation continued.
- `after_skill` compatibility handler moved to `legacy_event_compat_v1.py`.
- Legacy `TriggerRuntime` changed to lazy compatibility-only construction.
- Production path continues to use Generic Rule Runtime.
- Added lazy runtime boundary regression test.

## Tests
- 385 passed.
- Python compile PASS.

## Next
Continue item 1: isolate remaining direct Legacy APIs and remove proven production-dead manual execution paths without changing game behavior.
