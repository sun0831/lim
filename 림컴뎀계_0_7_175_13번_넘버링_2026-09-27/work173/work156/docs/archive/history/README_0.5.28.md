# 림컴뎀계 0.5.28

## 1턴 전체 출혈 상태공간 연결

0.5.27의 행동별 확률 합 계산을 확장하여, **한 행동의 출혈 Count 결과가 다음 행동의 입력 상태로 이어지는 1턴 DP 레이어**를 추가했다.

### 핵심 변경
- 요청된 행동 순서 전체를 따라 Bleed Count 확률 분포를 전달.
- 동일한 Bleed Count 상태는 합쳐서 계산하여 원시 Clash 경로를 전체 턴 단위로 열거하지 않음.
- 각 확률 합의 승/무/패 결과에서 발생한 총 Bleed proc을 다음 행동의 Count에 반영.
- `출혈 횟수 무한`에서는 Count 소비 없이 상태를 전달.
- 행동별로 다음 상태의 Bleed Count 분포와 기대 데미지를 기록.
- 후속 행동의 출혈 조건은 해당 분기에서 실제로 전달된 Count를 기준으로 평가.
- 각 행동의 가능한 출혈 proc 분포에는 기존 **하위 5% + 상위 5% 제거** 규칙을 적용.
- 기존 deterministic `turn_damage` 실행 결과는 변경하지 않고, 전체 턴 기대값을 별도 병렬 레이어에서 계산.
- 비확률 행동의 명시적 합 결과가 있으면 해당 출혈 소비를 다음 상태에 전달하고, 해당 행동의 기존 기대/실행 데미지도 전체 기대값에 포함.

### 결과 필드
- `turn_bleed_state`
  - `initial_bleed_count`
  - `final_bleed_distribution`
  - `expected_final_bleed_count`
  - `expected_turn_damage`
  - `expected_damage_by_identity`
  - `expected_damage_by_skill`
  - `actions[]`
    - `incoming_distribution`
    - `outgoing_distribution`
    - `expected_damage`
    - `branch_count`

### 중요한 범위
현재 상태공간의 핵심 축은 **Bleed Count**다. SP/코인/합 결과 및 출혈 소비를 행동 간에 연결하지만, 모든 게임 상태(자원·버프·적 HP·Stagger 등)를 확률 분기로 완전히 복제하는 단계는 아직 별도 확장 대상이다.

## 검증
- Python 문법 검사 PASS
- 통합 테스트 **71 passed**
