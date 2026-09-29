# 림컴뎀계 0.6.35 — Rule Runtime Trigger Migration

## 목적
기존 TriggerRule을 공통 Rule IR → RuleRuntime → EffectExecutor 경로로 실제 실행할 수 있는 migration boundary를 추가했다.

## 변경
- `RuleRuntime.execute_trigger_rules()` 추가
- Legacy `TriggerRule`을 `trigger_rule_to_ir()`로 변환 후 공통 Condition/Target/Effect 경로 사용
- resource/status 등 generic effect는 실제 실행
- 전문 action/legacy effect는 기존 specialized runtime과 공존 가능
- 기존 `TriggerRuntime` API는 변경하지 않음
- migration 전환을 검증하는 테스트 3개 추가

## 검증
- 신규/관련 테스트: 8 passed
- 전체 테스트: 330 passed
- Python syntax: PASS
