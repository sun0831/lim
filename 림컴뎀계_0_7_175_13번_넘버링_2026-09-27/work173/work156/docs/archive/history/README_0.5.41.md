# 림컴뎀계 0.5.41

## 핵심 변경

### 1. 출혈 5%/5% 절삭과 데미지의 상관관계 연결
- 턴 전체의 모든 확률 branch를 먼저 끝까지 전파한다.
- 누적 총 출혈 발동 횟수(`total_bleed_proc_distribution`)와 그 branch에서 발생한 누적 데미지를 함께 집계한다.
- 최종 출혈 발동 분포에서 하위 5%/상위 5%를 제거한 뒤, **같은 확률 질량을 해당 branch의 데미지에도 비례 적용**한다.
- 따라서 출혈 발동량과 데미지가 서로 상관되어 있을 때 단순히 `trimmed bleed × raw damage`로 계산하지 않고 실제 branch 상관관계를 보존한다.

### 2. 공동 통계 출력
`turn_bleed_state`에 `joint_bleed_proc_damage`를 추가했다.
- `probability`: 해당 총 출혈 발동량의 확률
- `damage_mass`: 해당 발동량에 귀속된 확률 가중 데미지
- `expected_damage_given_proc`: 해당 발동량 조건부 평균 데미지
- `retained_fraction`: 최종 5%/5% 절삭 후 남은 비율

### 3. 기대 데미지 결과 정리
- `expected_turn_damage_raw`: 절삭 전 전체 확률 평균 데미지
- `expected_turn_damage_trimmed`: 최종 중앙 90% branch를 기준으로 재가중한 데미지
- `expected_turn_damage`: UI에서 사용할 중앙 90% 기준 기대 데미지로 설정
- 기존 deterministic `turn_damage`는 변경하지 않음.

## 통계 처리 원칙
```text
전체 턴 확률 branch
  ↓
총 Bleed Proc + 누적 Damage 동시 집계
  ↓
총 Bleed Proc 분포에서 하위 5% / 상위 5% 제거
  ↓
동일한 branch 확률 질량을 Damage에도 적용
  ↓
중앙 90% 기대 Damage
```

중간 Clash/action에서 5% 절삭을 수행하지 않는다.

## 검증
- Python 문법 검사 통과
- 통합 테스트: **89 passed**
- 신규 회귀 테스트: `test_v29_joint_bleed_damage_trim.py`
