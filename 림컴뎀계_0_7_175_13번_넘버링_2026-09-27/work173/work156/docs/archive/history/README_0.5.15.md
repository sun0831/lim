# 림컴뎀계 0.5.15

## 이번 버전
특수자원의 **임계값 도달 → 조건 판정 → 효과 실행** 연결을 일반화했다.

### TriggerRuntime
- `resource_threshold_reached` 이벤트를 받을 수 있는 자원 조건 추가
  - `resource`
  - `resource_variant`
  - `resource_value`
  - `resource_delta_gte` / `resource_delta_lte`
- 시나리오의 `trigger_rules`를 런타임 규칙으로 추가 등록 가능

### Resource Trigger Effect
- `set_flag`
- `resource_gain`
- `resource_consume`
- `resource_set`
- `queue_action`

### 실행 순서
- 한 행동에서 발생한 임계값 이벤트를 행동 종료 후 처리
- 트리거가 다시 자원을 변경해 새 임계값 이벤트를 만들면 연쇄적으로 처리
- `queue_action`은 기존 ActionQueue를 통해 원본 행동 직후에 삽입
- 기존 사용자 지정 행동 순서는 변경하지 않음

### 검증
- Python compile: PASS
- 통합 테스트: **31 passed**

주의: 자동 추출된 특수자원 후보 35개는 여전히 검증 대기이며 자동 실행하지 않는다.
실제 게임 규칙이 확인된 규칙만 `trigger_rules`로 등록하는 구조다.
