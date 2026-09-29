# E35-4 Clause → RuleIR lowering

## Scope
E35-3의 미변환 Clause 중 반복 빈도가 높고 E34 Primitive로 표현 가능한 패턴을 보수적으로 RuleIR로 직접 lowering했다.

## Implemented lowering contracts
1. `skill_swap_timed`: 기본 스킬 변경, 슬롯 우선순위, 다음 턴 timing, invalidation 재발동 메타데이터
2. `forced_followup_action`: 사용 전/스킬 종료/공격 종료/턴 종료 등의 강제·후속 공격을 ActionQueue 계약으로 표현
3. `lowest_resource_selector`: 탄환/충전/호흡/정신력 등의 최저 자원 아군 대상 선택
4. `affiliation_target_selector`: 소속 기반 아군/적 대상 선택
5. `death_trigger_contract`: 사망 이벤트 기반 자원/상태 효과
6. `independent_rng_contract`: 탄환 등 개별 단위 RNG scope 보존

## Results
- Total clauses: **1103**
- Converted: **295**
- Unsupported: **808**
- Structural conversion rate: **26.75%**
- Unknown registry primitive contracts: **0**

This rate is structural Clause→RuleIR conversion coverage, not gameplay implementation coverage.

## Safety rule
Direct lowering is narrow and declarative. It does not add a new Runtime. Existing v29 parsing remains the fallback. Unmatched clauses remain unsupported instead of being fabricated.
