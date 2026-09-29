# 0.7.0 충전 역장 전수 대조 / Runtime 확장 — 2026-09-22

## 연결
- 적 처치 시 충전 역장 고정 획득
- 전투 시작 충전 위력 기반 충전 역장
- 전투 시작 `(기본 + 충전 위력)` 충전 역장
- 방어 스킬 사용 충전 역장 3 / 턴당 3회
- 2/3코인 적중 기반 다음 턴 충전 역장 예약
- 충전 소모 시 최저 HP 아군 충전 역장 3
- 충전 소모 시 자신 + 최저 충전 아군 2명 `(현재 충전 + 2)` / 최대 8 / 턴당 2회
- 기존 CCA 초과 충전 → 다음 턴 충전 역장 최대 3 경로 유지

## 경계
- `충전 역장`은 일반 Charge Count/Potency와 별도 Resource 유지
- RuleIR → EffectExecutor 공통 경계 사용
- 무작위 아군 / AEDD 고전압 외피 / 긴급 충전 역장은 별도 범위 검토 대상으로 유지하며, 거울던전 전용 규칙은 계산 대상에서 제외

## 테스트
- Charge Barrier targeted + 관련 회귀: 118 passed
- 신규 Charge Barrier identity tests 포함: 14 passed
- 184 identities catalog→GimmickRegistry 구성: 184/184 성공
- generic-safe catalog trigger rules: 64/64
