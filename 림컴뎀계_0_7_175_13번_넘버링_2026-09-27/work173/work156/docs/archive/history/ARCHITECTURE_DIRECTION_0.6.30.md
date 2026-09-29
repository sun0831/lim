# 림컴뎀계 0.6.30 — 기반 계층 연속 강화

기준 시각: 2026-09-20 03:37 KST

## 목적
0.6.29에서 추가한 Rule IR / 데이터 검증 / Golden Test 기반을 실제 기존 Runtime과 연결하기 전에, 마이그레이션과 미구현 규칙 추적에 필요한 기반을 강화한다.

## 이번 작업
- `rule_ir_bridge_v1.py`
  - legacy `TriggerRule` → `RuleIR`
  - legacy `GimmickRule` → `RuleIR`
  - 기존 Runtime을 유지한 채 점진적으로 IR로 이전할 수 있는 어댑터
  - legacy 전용 필드는 `legacy_gimmick` Effect로 보존
- `implementation_backlog_v1.py`
  - 184개 인격의 스킬/수비/패시브 텍스트에서 규칙 후보를 보수적으로 추출
  - 추출된 항목은 자동으로 구현/미구현 판정하지 않고 `unknown`으로 유지
  - 현재 후보 5,259개
- `RuleDependencyGraph`
  - 누락 dependency 탐지
  - dependency cycle 탐지
- 테스트 2개 추가

## 검증
- Python syntax: PASS
- 전체 테스트: 306 passed

## 다음 기반 작업
1. Rule IR ↔ 기존 TriggerRuntime의 실행 어댑터
2. 공통 Condition IR evaluator
3. 공통 Effect IR dispatcher
4. Target IR → TargetResolver 연결
5. DamageModifierRuntime 조건 표현력 확장
6. backlog 후보의 자동 분류 보조 도구(판정은 명시적으로 유지)
7. 주요 기믹 Golden Test 확대
