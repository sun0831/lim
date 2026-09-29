# 림컴뎀계 0.6.21

## 소속 축 범용 Runtime 추가

- `affiliation_runtime_v1.py` 추가
- 선택된 전투 편성에서 소속 구성원을 공통적으로 조회/선택할 수 있도록 분리
- 지원/원호 Runtime과 동일하게 소속 모듈은 대상 선택 로직을 직접 중복 구현하지 않도록 함
- 제공 기능:
  - 소속 보유 여부 확인
  - 활성/사망 포함 여부를 반영한 소속 구성원 조회
  - 소속 구성원 수 계산
  - 편성 순서 기반 정렬
  - 소속 내 최저값 1명/ N명 선택
  - 제외 인격 지정
- 기존 Ring Finger의 생체 재료 시작 시 소속 인원 계산을 `AffiliationResolver` 경유로 전환
- 기존 `ResourceRuntime`, `TriggerRuntime`, `ActionQueue`, `DamageRuntime` 역할은 변경하지 않음

## 설계 방향

`Affiliation Module -> AffiliationResolver -> 기존 Runtime`

형태로 소속별 규칙과 공통 소속 대상 선택을 분리한다.

이번 버전은 소속 규칙을 무리하게 대량 구현하지 않고, 이후 검계/엄지/검지/세븐/츠바이/리우/N사/W사/마침표/라만차랜드의 실제 규칙을 같은 기반 위에 올릴 수 있도록 공통 축을 먼저 확보한다.

## 회귀

- 기존 283 테스트 + 소속 Runtime 신규 3 테스트 = **286 passed**
- Python syntax check PASS
