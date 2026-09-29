# 0.7.103 — 거미집 엄지 아비 로쟈 `가속하는 미래` 오판 수정

실제 버프 원문과 `identity-10916` 인격 데이터를 대조하여 수정.

원문 기준:
- `Accelerating Future (Rodion)` 최대 5스택
- 기본 스킬 피해량 +3%/스택 (최대 15%)
- 기본 스킬 합 위력 +1/2스택
- 5스택에서 기본 스킬 코인 위력 +1
- 스킬 종료 시 효과 소멸

수정:
- `identity-10916`이 실제 합을 진행할 때 `가속하는 미래` 1스택 획득, 최대 5스택.
- 현재 스킬이 S1/S2/S3인 경우에만 Rodion 전용 스택 보정 적용.
- 합 위력은 floor(stack / 2).
- 피해량은 stack × 3%, 최대 15%.
- 5스택에서 코인 위력 +1.
- 스킬 종료 시 `가속하는 미래` 즉시 제거.
- 일반 `Accelerating Future`와 Rodion 전용 `Accelerating Future (Rodion)`을 동일 규칙으로 뭉개지 않음.
- 기존 `_execute_action_execution`의 `BuffDebuffRuntime` 누락 import도 함께 보완하여 관련 Clash 경로 회귀를 복구.

검증:
- 신규/관련 targeted regression: 66 passed.
- 전체 fast regression: 945 passed, 3 failed.
- 남은 3건은 이번 변경과 무관한 기존 문제:
  - `test_audit_0_7_83.py::test_charge_potency_haste_cap_uses_second_group`
  - `test_charge_potency_passive_runtime.py::test_10116_turn_end_haste_is_queued_to_next_turn_state`
  - `test_rule_ir_compiler_e35.py::test_e35_coverage_audit_has_no_unknown_registry_contracts`
