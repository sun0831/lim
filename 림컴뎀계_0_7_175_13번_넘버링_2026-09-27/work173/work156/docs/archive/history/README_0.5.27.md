# 림컴뎀계 0.5.27

## 1턴 기대 데미지 집계 연결

0.5.26의 확률 합 → 기대 출혈 발동량 → 합 결과별 기대 데미지 계산을 1턴 결과 집계까지 연결했다.

### 결과에 추가
- `expected_turn_damage`: 1턴 기대 데미지 합계
- `expected_damage_by_identity`: 인격별 기대 데미지
- `expected_damage_by_skill`: 인격/스킬별 기대 데미지
- 각 `actions[]`에 `expected_damage` 추가

### 계산 원칙
- 일반/고정 실행의 기존 `turn_damage`는 그대로 보존한다.
- `bleed_clash_probability`가 있는 행동은 해당 행동의 확률 합 결과에서 계산한 `expected_damage`를 기대값 집계에 사용한다.
- 확률 합 결과의 양 극단 5% 제거 규칙을 그대로 사용한다.
- `bleed_count_infinite`, 파불코, 99합 규칙 등 기존 출혈 규칙을 변경하지 않는다.

### 범위
이번 버전은 1턴 결과에 기대 데미지를 집계하는 단계다. 후속 행동의 조건/자원까지 각 확률 경로별로 완전히 분기하는 전체 상태공간 시뮬레이션은 별도 단계로 남겨 둔다.
