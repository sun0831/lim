# E35-3 Unsupported Clause Remediation Audit

## Purpose
E35-2에서 `RuleIR`로 직접 내려가지 못한 872개 clause를 보수적으로 분류한다.
이 분류는 구현률이 아니며, 새 Runtime을 만들기 전에 기존 E34 Primitive로 표현 가능한지 확인하기 위한 작업 우선순위 자료다.

## Result
| Classification | Count | Meaning |
|---|---:|---|
| existing_primitive_parser_gap | 712 | 기존 Primitive/Runtime으로 표현 가능성이 높지만 현재 v29 parser가 문장을 executable definition으로 만들지 못함 |
| data_or_parameter_gap | 90 | Primitive는 있으나 사망/부활/자원/대상/횟수/추가 피해 등의 세부 parameter contract가 부족 |
| compound_clause_decomposition | 68 | 한 문장에 조건+트리거+대상+효과+추가행동 등이 결합되어 있어 Clause를 여러 RuleIR로 분해해야 함 |
| true_runtime_gap | 2 | 현재 damage-engine 관점의 Rule vocabulary로 안전하게 표현하기 어려운 비전투 연출(BGM) |
| unresolved | 0 | 현재 보수적 분류에서 근거 부족 항목 없음 |

## Important
- 위 872개를 단순히 872개의 새 기능으로 해석하지 않는다.
- `existing_primitive_parser_gap`가 가장 크므로 새 Runtime 추가보다 parser/lowering 확장이 우선이다.
- `compound_clause_decomposition`은 E35 Compiler의 핵심 후속 작업이다.
- `data_or_parameter_gap`은 필요한 입력/상태 필드를 먼저 계약화한 뒤 구현해야 한다.
- BGM 2건은 1턴 피해 계산의 핵심 범위 밖이므로 구현률을 높이기 위해 Runtime을 추가하지 않는다.

## Representative cases
- `중지 작은 형님`: 기본 스킬 변경 → `SKILL_SWAP` + slot policy
- `거미집의 검`: 최저 체력 비율 거미집 아군에게 피해 전가 → `AffiliationResolver` + `TargetRuntime` + `EffectRuntime`
- `LCCB 대리`: 최저 탄환 아군의 마지막 탄환 → 공격 종료 추가 피해 → target/resource condition + `ActionQueue`/damage effect의 복합 RuleIR
- `거미집 엄지 아비`: 예지안 감소/0/과열/다음 턴 스킬 변경 → resource/state/turn lifecycle + `SKILL_SWAP` 조합

## Next
E35-4에서는 상위 반복 패턴을 parser에 무작정 추가하지 않고, 다음 순서로 RuleIR lowering contract를 추가한다.
1. Target/affiliation/lowest-resource compound lowering
2. Skill swap + slot policy + retry/next-turn timing
3. forced/follow-up/support/assist action lowering
4. resource/status threshold + consumption trigger composition
5. independent probability/RNG metadata
6. only then re-run the 872-clause audit
