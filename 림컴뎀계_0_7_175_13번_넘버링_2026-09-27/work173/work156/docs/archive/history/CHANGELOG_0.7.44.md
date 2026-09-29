# 0.7.44 — 20구 유로지비 료슈 「제.지」 정확 구현

## Source
- `identity_catalog_v2.json`
- identity: `identity-10409` / 20구 유로지비 료슈
- passive: `제.지`

## Source-backed behavior
1. 자신의 공격이 아닌 아군의 공격으로 적이 새롭게 흐트러짐 상태가 되면 발동.
2. 턴당 1회.
3. 20구 유로지비 료슈가 S1 `나사빠진 놈들`로 지원 공격.
4. 여러 적이 흐트러진 경우 체력이 가장 낮은 적을 대상으로 하며, 환상체는 본체 우선 후 부위.
5. 이 패시브로 생성된 S1에서 코인 효과로 자신이 얻는 진동 횟수에 +1.
6. 해당 지원 S1의 마지막 코인 적중 시 진동 폭발.
7. 진동 폭발 자체에는 Count 감소를 암묵적으로 추가하지 않음.

## Implementation
- 기존 일반 `stagger_assist`에 섞지 않고 `ryoshu_10409_stagger_assist` identity-local rule kind로 분리.
- Trigger: `after_skill` + `identity_id_not(owner)` + `newly_staggered`.
- Generated action: S1 `1040901`, `trigger_kind=ryoshu_10409_stagger_assist`.
- Target policy: `lowest_hp_staggered`.
- Generated action의 coin-level Tremor Count gain에만 +1 적용; skill-level `[사용시]` gain에는 적용하지 않음.
- 마지막 coin에서 Tremor Burst 실행; implicit Count cost 없음.
- enemy target pool에 실제 EnemyState 참조를 유지하여 staggered selector가 상태를 확인할 수 있도록 수정.

## Validation
- New/exact tests: 5/5
- Tremor/Amplitude/RuleIR/support/target regression: 126/126
- Existing unrelated `test_triggers_actions_queue.py` 2 failures were not caused by this change; they are the pre-existing FakeEngine `simulate_coin(..., is_added_coin=...)` signature mismatch.
