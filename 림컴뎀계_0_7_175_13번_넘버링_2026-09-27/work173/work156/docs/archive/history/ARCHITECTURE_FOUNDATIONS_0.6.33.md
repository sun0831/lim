# 림컴뎀계 0.6.33 — 최적화 단계: 공통 조건/활성화/마이그레이션 경계 강화

기준 시각: 2026-09-20 KST

## 목적
0.6.32의 Rule IR / Condition / Effect / Target 기반을 실제 기존 런타임과 더 강하게 연결하되, 전투 결과를 만드는 기존 mutation path는 유지한다.

## 이번 변경
- `TriggerRuntime.condition_met()`가 `ConditionRuntime`을 단일 위임 경로로 사용.
  - 기존/신규 Condition semantics 이중 구현 제거.
  - 조건 연산자 추가 시 두 런타임이 따로 드리프트하지 않도록 함.
- `ConditionRuntime`에 기존 TriggerRuntime의 주요 조건 연산자를 추가.
  - support target, ammo, resource threshold/crossing, received-target HP/death/damage, killer/lowest-ammo 등.
- `RuleIR.activation_scope` 추가.
  - `global`, `per_identity`, `per_actor`, `per_skill`, `per_target`, `per_identity_target` 계열을 IR 자체가 보존.
- `activation_runtime_v1.py` 추가.
  - Rule IR의 activation limit을 실제 공통 runtime에서 처리.
  - turn reset 지원.
- `RuleRuntime`이 activation runtime을 사용하도록 연결.
- `GimmickRule -> RuleIR` 변환 개선.
  - stagger/skill/actor 조건을 공통 `ConditionIR`로 변환.
  - Python `hash()` 대신 SHA-1 기반 안정적 rule ID 사용.
- `rule_ir_migration_v1.py` 추가.
  - legacy Trigger/Gimmick rule의 IR 변환량과 condition/target/effect coverage를 측정.
- `EffectRuntime`의 주요 legacy effect category 인식 범위 확대.
- 회귀/마이그레이션/activation 테스트 추가.

## 검증
- Python syntax: PASS
- 전체 테스트: **324 passed**

## 최적화 의미
이번 단계의 핵심은 기능 추가량보다 **중복 규칙 해석 제거 + 공통 IR의 실제 사용 범위 확대 + migration 측정 가능성 확보**다.
