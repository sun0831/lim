# 0.7.19 — 진폭 후속 효과 실전 Runtime 연결

## 핵심
- 진폭 상태 자체는 기존 `Target.statuses["Amplitude"]` 단일 저장 구조 유지.
- 진폭 존재 조건으로 발동하는 피해량 증감(`ModifyContext`)이 실제 `PassiveRuntime` 실행 경로에서 동작하는지 검증.
- 진폭 변환 후 동일 대상의 후속 진폭 조건 피해 보정이 연속 이벤트에서 읽히는지 검증.
- 진폭이 없는 경우 조건부 피해 보정이 발동하지 않는지 검증.
- 별도의 `AmplitudeDamageRuntime`를 추가하지 않고 기존 `Condition + ModifyContext` 공통 계약을 재사용.

## 검증
- 진폭/진동 관련 테스트: 24 passed
- 기존 진폭 RuleIR 실행 테스트 포함
- 기존 Tremor Burst 회귀 테스트 포함

## 주의
- 실제 카탈로그에 없는 진폭별 수치/변환비/소모량은 추가하지 않음.
- `진폭 변환` 자체는 명시적인 진동 소모를 추론하지 않음.
