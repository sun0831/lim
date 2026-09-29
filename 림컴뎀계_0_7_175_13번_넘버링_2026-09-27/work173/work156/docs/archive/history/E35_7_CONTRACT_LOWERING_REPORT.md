# E35-7 Contract Lowering

## 목적
E35-6에서 안전하게 lowering하지 못했던 Clause 중, 기존 E34 Primitive 계약으로 표현 가능하지만 v29 parser가 놓치는 **고신뢰 단일-fragment 패턴**을 별도 계약 계층에서 lowering했다.

## 원칙
- 기존 v29 parser가 먼저 실행된다.
- v29가 처리하지 못한 Clause에만 E35-7 contract lowering을 적용한다.
- 새 Runtime/Primitive family는 추가하지 않는다.
- 불명확한 문장은 계속 unsupported로 남긴다.
- 수치/효과/트리거가 명시적인 경우에만 lowering한다.

## 결과
- 전체 Clause: 1,103
- E35-6 기준 RuleIR 변환: 295
- E35-7 이후 RuleIR 변환: **314**
- 추가 변환: **19**
- 구조적 변환률: **28.47%**
- 잔여 미변환: **789**
- Registry 미등록 contract: **0**

이 수치는 게임 기믹 구현률이 아니라 Clause → RuleIR 구조 변환률이다.

## 사용 Primitive contracts
- resource_effect
- status_effect
- damage_modifier_effect
- condition_resource_predicate
- condition_threshold
- condition_action_state

## 안전성
E35-7은 기존 parser 결과를 덮어쓰지 않는다. 따라서 기존 RuleIR의 effect kind, deferred metadata 등의 계약을 변경하지 않는다.

## 테스트
- E35-6/E35-7/E35 compiler/E34 registry/axis regression: **53 passed**
