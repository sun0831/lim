# 0.7.28 — 진동 부여량 Modifier 공통 연결

- `진동` 부여의 canonical mutation boundary에 event-scoped `tremor_potency_bonus` / `tremor_count_bonus` 적용을 유지.
- `대상에게 시선이 있으면, 이 스킬에서 부여하는 출혈, 진동 위력 +2` 패턴을 공통 RuleIR로 컴파일.
- `대상에게 시선이 있으면`은 대상(`enemy`)의 `시선` 상태를 검사.
- `이 스킬에서 부여하는 진동 위력 +N/횟수 +N`은 현재 이벤트의 Tremor application modifier로만 적용.
- 일반 `위력 +N` parser가 위 문장을 `clash_power_bonus`로 잘못 해석하지 않도록 차단.
- 기존 Tremor/Burst 회귀 테스트 유지.
