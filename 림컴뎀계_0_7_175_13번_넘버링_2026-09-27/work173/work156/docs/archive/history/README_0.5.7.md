# 림컴뎀계 0.5.7

## 핵심 변경

### 1. 범용 Trigger → Condition → Effect 런타임
`trigger_runtime_v1.py`를 추가했다.

- TriggerRule: 어떤 이벤트를 감시하는지 정의
- TriggerCondition: 스킬/흐트러짐/자원/상태 등의 조건 정의
- TriggerEffect: 보조공격 생성, 자원 증가, 추가 피해 등 결과 정의
- 턴당 발동 횟수와 rule id를 추적

기존 `GimmickRegistry`의 보수적 자연어 파싱은 유지하면서, **실제 발동 판정은 선언형 TriggerRuntime을 거치도록** 변경했다.

### 2. 사용자 행동과 파생 행동의 완전 분리 유지
사용자 입력 `actions`는 requested order로 고정한다.
패시브/스킬/흐트러짐에서 발생한 공격은 ActionQueue의 generated action으로 즉시 삽입한다.

### 3. 흐트러짐 조건 일반화
`newly_staggered` 조건으로
- 공격 시작: 비흐트러짐
- 공격 종료: 흐트러짐
을 하나의 범용 조건으로 처리할 수 있다.

### 4. 결과 추적
solve 결과에 `trigger_rules`를 추가하여 실제 계산에 사용된 선언형 규칙을 확인할 수 있다.

## 검증
17개 테스트 전부 통과.
