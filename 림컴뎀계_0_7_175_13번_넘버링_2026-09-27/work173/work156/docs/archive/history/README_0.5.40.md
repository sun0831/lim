# 림컴뎀계 0.5.40

## 핵심 변경

### 1. 출혈 극단값 5% 절삭을 턴 전체 기준으로 변경
- 이전: 각 확률형 행동마다 출혈 발동 분포를 5%/5% 절삭.
- 변경: 한 턴의 모든 요청 행동과 확률 분기를 끝까지 전파한 뒤, **누적 총 출혈 발동 횟수 분포**에 한 번만 하위 5%/상위 5% 절삭.
- 중간 확률분기는 절삭하지 않으므로 이후 행동의 출혈 Count/상태 계산을 왜곡하지 않음.
- `total_bleed_proc_distribution`: 절삭 전 누적 출혈 발동 분포
- `trimmed_bleed_proc_distribution`: 중앙 90% 분포
- `expected_bleed_procs_raw`: 절삭 전 기대 출혈 발동 횟수
- `expected_bleed_procs_trimmed`: 중앙 90% 기준 기대 출혈 발동 횟수
- `trim_scope`: `whole_turn_final_bleed_proc_distribution`

### 2. Clash 규칙 정정
- Draw(T): 양쪽 코인 모두 유지.
- 99번째 Clash: **무조건 적 승리(L)**.
- `max_exchanges`를 99보다 작게 설정한 테스트/시뮬레이션에서는 마지막 교환을 강제로 적 승리로 바꾸지 않음. 실제 99번째에만 강제 규칙 적용.

### 3. 확률형 Clash 상태 전파 유지
- W/T/L branch별 SP, 자원, 상태, HP/Stagger, Trigger activation 상태를 유지.
- 다음 Clash 확률은 직전 branch의 변경된 상태로 재계산.
- 누적 Bleed Proc 축을 별도로 유지하여 턴 전체 출혈 분포를 정확히 집계.

## 주의
- `expected_turn_damage`는 현재 branch 전체를 그대로 평균낸 값이며, 5% 절삭은 **출혈 발동 횟수 통계**에 적용된다.
- 즉 출혈 절삭으로 인해 데미지까지 자동으로 재가중하려면 향후 `누적 총 출혈 발동량 ↔ 누적 피해` 공동분포가 추가로 필요하다.
- deterministic `turn_damage` 계산은 기존 권위 경로를 유지한다.

## 검증
- Python 문법 검사 통과
- 통합 테스트: **88 passed**
