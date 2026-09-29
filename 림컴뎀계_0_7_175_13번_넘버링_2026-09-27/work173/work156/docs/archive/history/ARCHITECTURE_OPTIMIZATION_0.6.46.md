# 림컴뎀계 0.6.46 — Golden Rule Parity Layer

## 이번 변경

실제 Legacy TriggerRule과 migration-safe Rule IR 실행 경로를 동일 입력에서 독립 실행해 비교하는 Golden Parity 계층을 추가했다.

비교 기준:
- rule_id / event
- 발동된 effect payload
- activation count
- scoped activation bucket
- migration safety

Legacy TriggerRuntime은 effect payload를 반환하고, IR 경로는 실제 generic EffectExecutor까지 실행하므로, 두 경로의 **의도된 effect payload와 activation semantics**를 우선 parity 기준으로 고정한다. 실제 상태 mutation은 EffectExecutor의 기존 unit/integration 테스트가 별도로 검증한다.

## 추가 파일

- `golden_rule_parity_v1.py`
- `test_v93_golden_rule_parity.py`

Golden cases:
- resource gain
- status gain
- damage modifier
- flag/set_flag
- per-identity activation
- failed condition activation preservation

## 검증

- Golden focused: **6 passed**
- Migration/integration regression 포함: **10 passed**
- 전체 회귀: **355 passed**
- 이전: 349 passed
- 증가: **+6 tests**

## 다음 단계

Golden parity를 실제 catalog에서 생성되는 migration-safe Rule들까지 확장하고, parity가 고정된 Rule부터 Legacy 실행 분기를 제거한다.
