# 림컴뎀계 0.7.0 E23 — 프로젝트 공유용 인계 문서

## 기준
- 기준 버전: 림컴뎀계 0.7.0
- 단계: E23
- 이전 산출물: 림컴뎀계_0.7.0_E22.zip
- Gap 원본: GIMMICK_GAP_REPORT_v4.md.json
- 현재 작업 원칙: 인격별 하드코딩보다 Clause → Semantic Cluster → 기존 Primitive 대조 → 실제 Gap만 신규 Primitive → RuleIR 등록 순서로 공통화한다.

## E23에서 확인한 사실
전체 Gap corpus의 skill_transform 태그 레코드는 26개이다. 기존 22개는 부분 집계였으며 E23의 분모로 사용하지 않는다. 26개 레코드를 보수적으로 clause 분해하여 66개 skill 관련 후보를 얻었다.

### Clause 분류
- unresolved: 31
- conditional_skill_trigger: 15
- true_skill_swap: 6
- skill_reclassify: 5
- next_turn_skill_swap: 4
- forced_or_followup_skill: 3
- coin_or_power_transform: 2

주의: 위 분류는 clause 후보 기준이며 원본 레코드 단위 합계와 동일한 의미가 아니다.

## 확정된 Primitive 경계
1. SKILL_SWAP
   - 실제 스킬 A를 스킬 B로 교체.
   - EffectIR kind `skill_swap`으로 매핑.
2. SKILL_RECLASSIFY
   - 스킬 자체를 교체하지 않고 특정 종류/분류의 스킬로 취급.
3. FORCED_OR_FOLLOWUP_SKILL
   - 추가/강제/후속 스킬 행동. Action/Trigger 계열로 분리.
4. COIN_OR_POWER_TRANSFORM
   - 스킬 자체를 교체하지 않고 코인/위력 등을 변경. 별도 Transform 계열.

### 조합으로 처리할 것
- NEXT_TURN_SKILL_SWAP = next-turn timing/state condition + SKILL_SWAP
- RESOURCE_TRIGGERED_SKILL_SWAP = resource condition + generic SKILL_SWAP
따라서 resource가 스킬 교체의 기본 소유권을 가져서는 안 된다.

## E23 구현
- `resource_primitive_v1.py`에 `ResourcePrimitive.SKILL_SWAP = skill_swap` 추가.
- EffectIR kind `skill_swap` → primitive 매핑 추가.
- 기존 `RESOURCE_TRIGGERED_SKILL_SWAP`은 호환성을 위해 유지.
- E23 집중 테스트: 3 passed.
- 전체 suite는 이전 환경에서 장시간/timeout 문제가 있어 E23에서 전체 PASS로 보고하지 않음.

## 현재 Resource 축 진행 위치
E20 trigger 재분해 ✓
E21 selector 대칭/파라미터 ✓
E22 resource consumption 감사 ✓
E23 skill transform 감사 ✓
E24 non_resource_or_special 86건 재감사 ← 다음
E25 resource conversion/exchange 재검토
E26 status_effect_side_clause 149건 Resource 축에서 제외 및 Buff/Status Runtime으로 이관 기록

## 다음 단계 E24 작업 규칙
- 86건을 신규 primitive 86개로 취급하지 않는다.
- 각 문장을 clause 수준으로 재분해한다.
- 먼저 기존 Primitive(`SKILL_RECLASSIFY`, `SKILL_SWAP`, resource/target/condition/effect 계열)와 대조한다.
- 실제로 새로운 의미가 있는 경우에만 신규 Primitive 후보로 남긴다.
- `status_effect_side_clause` 149건은 E24에서 섞지 않는다.
- 축별 숫자는 분모를 명시하고, 후보 탐지 수와 실행 가능 coverage를 혼동하지 않는다.

## 이후 전체 루트
Phase 1: resource_transform 잔여 gap E20~E26
Phase 2: cross_identity → target_selection → stack_threshold → skill_transform → multi_target → probability_random → special_state
Phase 3: Primitive Registry 확정 → Clause→Primitive→RuleIR compiler → 621 attack skills + 588 passives 회귀
Phase 4: Bleed/Unbreakable Coin → identity data bulk integration → real-game golden validation

## 중요한 원칙
- 8개 축은 8개 Runtime을 만든다는 뜻이 아니다.
- 다른 축에서 이미 존재하는 Primitive와 의미가 겹치면 기존 Primitive을 재사용/확장한다.
- Primitive가 실제 실행 가능한지 여부와 semantic classification 여부를 별도 지표로 관리한다.
- identity-specific hardcoding은 공통 Primitive로 표현할 수 없는 경우에만 마지막 수단으로 사용한다.
