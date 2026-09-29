# E34 — Primitive Registry / Contract Freeze

## 목표
E17-E33에서 실제 계약으로 확인된 Primitive를 하나의 조회 가능한 Registry로 고정한다.
각 분석축을 별도 Runtime으로 만들지 않으며, 실행은 기존 Condition/Target/Effect/Action/Trigger/Resource 계층이 담당한다.

## 구현
- `primitive_registry_v1.py`
  - `PrimitiveContract`
  - `PrimitiveFamily`
  - `PrimitiveRegistry`
  - `DEFAULT_REGISTRY`
  - Effect kind → 기존 `resource_primitive_v1` → Registry 해석 경로
- `PRIMITIVE_CONTRACT_FREEZE_E34.json`
  - E17-E33에서 확정된 13개 Resource Primitive 계약 동결
  - 신규 Runtime 0개
- `test_primitive_registry.py`
  - Registry 중복/누락 검증
  - Resource conversion 매핑 검증
  - resource-triggered skill swap의 기존 Runtime 조합 검증
  - highest/lowest target 공통 owner 검증
  - freeze 파일과 Registry 일치 검증

## 검증
- E34 Registry 관련 테스트 + 기존 Primitive 회귀 + resource primitive 회귀: **67 passed**
- 전체 571개 테스트는 이번 단계에서 실행하지 않음. 변경 범위가 Primitive Registry 및 계약 파일에 한정되므로 영향 범위 테스트만 실행했다.

## 원칙
- Audit axis ≠ Runtime
- 중복 Primitive는 Registry에서 하나의 canonical id로 관리
- 실제 계약 공백이 확인될 때만 새 Primitive를 추가
- Legacy는 E34에서 제거하지 않음. E35 RuleIR Compiler 및 E36 전체 회귀 후 퇴역 판단

## E35-1 — Clause → RuleIR Compiler

- Added `rule_ir_compiler_v1.py`.
- Compiles canonical `passive_compiler_v29` clause output into `RuleIR`.
- Preserves source text, deferred-turn metadata, parser reasons, unsupported reasons,
  condition/effect structural values, and primitive contract routing IDs.
- No new Runtime introduced.
- Added `test_rule_ir_compiler_e35.py`.
- Focused regression: 46 passed.
- RuleIR foundation/migration/legacy-boundary + E34 regression: 122 passed.
