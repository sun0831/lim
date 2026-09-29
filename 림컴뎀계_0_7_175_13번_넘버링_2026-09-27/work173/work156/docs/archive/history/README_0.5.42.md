# 림컴뎀계 0.5.42

## 출혈 계산 마무리

- Bleed 5%/5% 극단값 절삭은 **턴 전체 확률 전파가 끝난 뒤 1회** 적용한다.
- 중간 Clash/action 분포는 절삭하지 않고 다음 행동으로 그대로 전달한다.
- 총 Bleed Proc와 누적 데미지를 같은 branch에서 추적하여 최종 절삭 시 상관관계를 보존한다.
- 최종 Count 분포는 `initial_count - total_proc`로 단순 환산하지 않는다.
  - 턴 중 Bleed 획득
  - `bleed_count_infinite`
  - 기타 상태 변화가 있어도 실제 terminal branch의 Count를 사용한다.
- `expected_final_bleed_count_trimmed`와 `trimmed_final_bleed_distribution`을 제공한다.
- action-local `bleed_probability`의 trim 값은 진단용이며, **턴 최종 기대값의 권위 있는 절삭은 `turn_bleed_state`**에서 수행한다.
- 99번째 Clash는 실제 `max_exchanges=99`일 때만 적 승리로 강제된다.
- Draw는 양쪽 코인을 유지한다.

## 검증

- Python 문법 검사 통과
- 통합 테스트: **92 passed**
