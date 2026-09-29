# 림컴뎀계 0.6.8

0.6.8은 1턴 분석 결과의 원인 추적성을 강화한 패치입니다.

### 핵심
- Action별 `state_diff`가 이제 HP/SP/충전/탄환뿐 아니라
  Stagger, 상태이상, Poise, 특수자원의 추가·소모·변경까지 노출합니다.
- 상태 변화는 `before → after`로 기록되어 결과가 달라졌을 때 어느 상태가 원인이었는지 직접 확인할 수 있습니다.
- 0.6.6의 Requested → Resolved → Triggered Action 구조와 호환됩니다.

### 검증
- 전체 테스트 통과: 250개
