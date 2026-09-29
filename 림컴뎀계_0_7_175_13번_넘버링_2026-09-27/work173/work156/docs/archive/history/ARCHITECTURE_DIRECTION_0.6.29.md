# 림컴뎀계 0.6.29 — 최신 아키텍처 적용 방향

기준 시각: 2026-09-20 03:37 KST

## 이번 버전의 목적
기존 계산 규칙을 대규모로 다시 작성하지 않고, 최신 설계 방향을 실제 코드/데이터 구조에 먼저 반영한다.

## 적용
- `rule_ir_v1.py`: Trigger / Condition / Target / Effect / Timing / Activation / Dependency / Status를 표현하는 공통 Rule IR 추가.
- `data_validation_v1.py`: 기존 `identity_catalog_v2.json` 구조 검증 기반 추가.
- `golden_test_runtime_v1.py`: 핵심 결과를 안정적으로 비교할 Golden Test 기반 추가.
- `data/identities/*.json`: 기존 184개 인격을 12명 수감자 단위의 구조화된 source view로 생성. 원본 catalog를 대체하지 않으며 generated view임을 명시.
- 기존 TriggerRuntime / GimmickRule / DamageModifierRuntime은 호환성을 유지한다.

## 다음 단계
1. Rule IR을 기존 GimmickRule/TriggerRule과 점진적으로 연결
2. Condition/Effect/Target 공통 계층을 실제 Runtime에서 재사용
3. DamageModifierRuntime에 상태/자원/공격조건 표현력 확대
4. 구현 상태 및 미구현 규칙 backlog 자동 생성
5. 주요 기믹을 Golden Test로 고정
6. 이후 수감자별 generated view를 사람이 검수 가능한 structured rule data로 점진적으로 승격

## 검증
- 인격 데이터: 184개
- 수감자 파일: 12개
- 전체 테스트: 304 passed
