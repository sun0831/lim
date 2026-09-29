# 림컴뎀계 0.6.20

## 지원/원호 공격 범용 런타임 분리

- `support_runtime_v1.py` 추가
- 원호/지원 공격의 **행동자 선택**과 **스킬 선택**을 공통 resolver로 분리
- 지원 행동자 정책:
  - `fixed`
  - `ally_left`
  - `ally_right`
  - `next_available_ally`
- 지원 스킬 정책:
  - `named`
  - `requested_next`
  - `first_attack`
- 공통 `assist` / `stagger_assist` / 좌우 지원 명령이 `support_action` effect를 사용하도록 변경
- 피쿼드 선장의 우측 원호도 동일 resolver 사용
- 기존 `queue_action` 호환 경로는 유지
- 기존 ActionQueue / TriggerRuntime / DamageRuntime의 역할은 변경하지 않음

## 회귀

- 기존 280 테스트 + 지원 런타임 신규 3 테스트 = **283 passed**
- Python syntax check PASS
- 전체 통합 테스트 PASS

## 설계 원칙

원호 공격을 인격별 분기문으로 구현하지 않고:

`TriggerRule -> support_action -> SupportActionResolver -> GimmickAction -> ActionQueue`

형태로 통일한다.

이를 통해 향후 검계/엄지/검지/협회 계열에서 원호·지원·추격·좌우 아군 지정 효과가 추가되어도 동일 런타임을 재사용할 수 있다.
